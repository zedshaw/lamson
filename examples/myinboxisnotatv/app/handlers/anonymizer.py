from config.settings import relay, BOUNCES, SPAM, CONFIRM
from lamson.routing import route, Router, route_like
from lamson.bounce import bounce_to
from lamson.spam import spam_filter
from lamson import view, queue, confirm
from app.model import filter, addressing
import logging


@route(".+")
def IGNORE_BOUNCE(message):
    bounces = queue.Queue(BOUNCES)
    bounces.push(message)
    return START

@route(".+")
def SPAMMING(message):
    return SPAMMING

@route("start@(host)")
@route("(user_id)@(host)")
@bounce_to(soft=IGNORE_BOUNCE, hard=IGNORE_BOUNCE)
@spam_filter(SPAM['db'], SPAM['rc'], SPAM['queue'], next_state=SPAMMING)
def START(message, user_id=None, host=None):
    if user_id:
        market_anon = addressing.mapping(message['from'], 'marketroid', host)

        reply = filter.cleanse_incoming(message, user_id, host, market_anon)
        relay.deliver(reply)

        return DEMARKETING
    else:
        CONFIRM.send(relay, "start", message, "mail/start_confirm.msg", locals())
        return CONFIRMING


@route("start-confirm-(id_number)@(host)")
def CONFIRMING(message, id_number=None, host=None):
    original = CONFIRM.verify('start', message['from'], id_number)

    if original:
        user_anon = addressing.mapping(message['from'], 'user', host)

        welcome = view.respond(locals(), "mail/welcome.msg", 
                           From=user_anon,
                           To=message['from'],
                           Subject="Welcome to MyInboxIsNotA.TV")
        relay.deliver(welcome)

        return PROTECTING
    else:
        logging.warning("Invalid confirm from %s", message['from'])
        return CONFIRMING


@route("(user_id)@(host)")
def DEMARKETING(message, user_id=None, host=None):
    reply = filter.cleanse_incoming(message, user_id, host)
    relay.deliver(reply)
    return DEMARKETING


@route("(marketroid_id)@(host)")
@route("(user_id)@(host)")
def PROTECTING(message, marketroid_id=None, host=None, user_id=None):
    if user_id:
        logging.warning("Attempted user->user email from %r", message['from'])
        forbid =  view.respond(locals(), "mail/forbid.msg",
                               From="noreply@%(host)s",
                               To=message['from'],
                               Subject="You cannot email another user or yourself.")
        relay.deliver(forbid)
    else:
        reply = filter.route_reply(message, marketroid_id, host)
        relay.deliver(reply)

    return PROTECTING

