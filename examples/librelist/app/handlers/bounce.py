from config.settings import relay, CONFIRM
from lamson.routing import route, Router, route_like
from lamson.bounce import bounce_to
from app.model import mailinglist, bounce
from app import handlers
from email.utils import parseaddr



def force_to_bounce_state(message):
    # set their admin module state to disabled
    name, address = parseaddr(message.bounce.final_recipient)
    Router.STATE_STORE.set_all(address, 'BOUNCING')
    Router.STATE_STORE.set('app.handlers.bounce', address, 'BOUNCING')
    mailinglist.disable_all_subscriptions(message.bounce.final_recipient)

@route(".+")
def BOUNCED_HARD(message):
    if mailinglist.find_subscriptions(message.bounce.final_recipient):
        force_to_bounce_state(message)

    bounce.archive_bounce(message)
    return handlers.admin.START

@route(".+")
def BOUNCED_SOFT(message):
    if mailinglist.find_subscriptions(message.bounce.final_recipient):
        force_to_bounce_state(message)
        msg = bounce.mail_to_you_is_bouncing(message)
        relay.deliver(msg)

    bounce.archive_bounce(message)
    return handlers.admin.START


@route('unbounce@(host)')
def BOUNCING(message, host=None):
    CONFIRM.send(relay, 'unbounce', message, 'mail/unbounce_confirm.msg',
                      locals())

    return CONFIRMING_UNBOUNCE


@route('unbounce-confirm-(id_number)@(host)')
def CONFIRMING_UNBOUNCE(message, id_number=None, host=None):
    original = CONFIRM.verify('unbounce', message['from'], id_number)

    if original:
        relay.deliver(bounce.you_are_now_unbounced(message))
        name, address = parseaddr(message['from'])
        Router.STATE_STORE.set_all(address, 'POSTING')
        mailinglist.enable_all_subscriptions(message['from'])
        return UNBOUNCED

@route('unbounce@(host)')
def UNBOUNCED(message, host=None):
    # we just ignore these since they may be strays
    return UNBOUNCED


