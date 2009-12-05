from email.utils import parseaddr
from config.settings import relay, SPAM, CONFIRM
import logging
from lamson import view, queue
from lamson.routing import route, stateless, route_like, state_key_generator
from lamson.bounce import bounce_to
from lamson.server import SMTPError
from lamson.spam import spam_filter
from app.model import mailinglist, bounce, archive
from app.handlers import bounce


INVALID_LISTS = ["noreply", "unbounce"]


@state_key_generator
def module_and_to(module_name, message):
    name, address = parseaddr(message['to'])
    if '-' in address:
        list_name = address.split('-')[0]
    else:
        list_name = address.split('@')[0]

    return module_name + ':' + list_name


@route("(address)@(host)", address='.+')
def SPAMMING(message, **options):
    return SPAMMING


@route('(bad_list)@(host)', bad_list='.+')
@route('(list_name)@(host)')
@route('(list_name)-subscribe@(host)')
@bounce_to(soft=bounce.BOUNCED_SOFT, hard=bounce.BOUNCED_HARD)
@spam_filter(SPAM['db'], SPAM['rc'], SPAM['queue'], next_state=SPAMMING)
def START(message, list_name=None, host=None, bad_list=None):
    if bad_list:
        if '-' in bad_list:
            # probably put a '.' in it, try to find a similar list
            similar_lists = mailinglist.similar_named_lists(bad_list.replace('-','.'))
        else:
            similar_lists = mailinglist.similar_named_lists(bad_list)

        help = view.respond(locals(), "mail/bad_list_name.msg",
                            From="noreply@%(host)s",
                            To=message['from'],
                            Subject="That's not a valid list name.")
        relay.deliver(help)

        return START

    elif list_name in INVALID_LISTS or message['from'].endswith(host):
        logging.debug("LOOP MESSAGE to %r from %r.", message['to'],
                     message['from'])
        return START

    elif mailinglist.find_list(list_name):
        action = "subscribe to"
        CONFIRM.send(relay, list_name, message, 'mail/confirmation.msg',
                          locals())
        return CONFIRMING_SUBSCRIBE

    else:
        similar_lists = mailinglist.similar_named_lists(list_name)
        CONFIRM.send(relay, list_name, message, 'mail/create_confirmation.msg',
                          locals())

        return CONFIRMING_SUBSCRIBE

@route('(list_name)-confirm-(id_number)@(host)')
def CONFIRMING_SUBSCRIBE(message, list_name=None, id_number=None, host=None):
    original = CONFIRM.verify(list_name, message['from'], id_number)

    if original:
        mailinglist.add_subscriber(message['from'], list_name)

        msg = view.respond(locals(), "mail/subscribed.msg",
                           From="noreply@%(host)s",
                           To=message['from'],
                           Subject="Welcome to %(list_name)s list.")
        relay.deliver(msg)

        CONFIRM.cancel(list_name, message['from'], id_number)

        return POSTING
    else:
        logging.warning("Invalid confirm from %s", message['from'])
        return CONFIRMING_SUBSCRIBE


@route('(list_name)-(action)@(host)', action='[a-z]+')
@route('(list_name)@(host)')
@spam_filter(SPAM['db'], SPAM['rc'], SPAM['queue'], next_state=SPAMMING)
def POSTING(message, list_name=None, action=None, host=None):
    if action == 'unsubscribe':
        action = "unsubscribe from"
        CONFIRM.send(relay, list_name, message, 'mail/confirmation.msg',
                          locals())
        return CONFIRMING_UNSUBSCRIBE
    else:
        mailinglist.post_message(relay, message, list_name, host)
        # archive makes sure it gets cleaned up before archival
        final_msg = mailinglist.craft_response(message, list_name, 
                                               list_name + '@' + host)
        archive.enqueue(list_name, final_msg)
        return POSTING
    

@route_like(CONFIRMING_SUBSCRIBE)
def CONFIRMING_UNSUBSCRIBE(message, list_name=None, id_number=None, host=None):
    original = CONFIRM.verify(list_name, message['from'], id_number)

    if original:
        mailinglist.remove_subscriber(message['from'], list_name)

        msg = view.respond(locals(), 'mail/unsubscribed.msg',
                           From="noreply@%(host)s",
                           To=message['from'],
                           Subject="You are now unsubscribed from %(list_name)s.")
        relay.deliver(msg)

        CONFIRM.cancel(list_name, message['from'], id_number)

        return START
    else:
        logging.warning("Invalid unsubscribe confirm from %s", message['from'])
        return CONFIRMING_UNSUBSCRIBE


@route("(address)@(host)", address=".+")
@spam_filter(SPAM['db'], SPAM['rc'], SPAM['queue'], next_state=SPAMMING)
def BOUNCING(message, address=None, host=None):
    msg = view.respond(locals(), 'mail/we_have_disabled_you.msg',
                       From='unbounce@librelist.com',
                       To=message['from'],
                       Subject='You have bounced and are disabled.')
    relay.deliver(msg)
    return BOUNCING

