from app.model import post, comment
from email.utils import parseaddr
from config.settings import relay, SPAM, CONFIRM
from lamson import view, queue
from lamson.routing import route, stateless
from lamson.spam import spam_filter
import logging



@route("(user_id)-AT-(domain)-(post_name)-comment@(host)")
def SPAMMING(message, **options):
    return SPAMMING


@route("(user_id)-AT-(domain)-(post_name)-comment@(host)")
@spam_filter(SPAM['db'], SPAM['rc'], SPAM['queue'], next_state=SPAMMING)
def START(message, user_id=None, post_name=None, host=None, domain=None):
    comment.attach_headers(message, user_id, post_name, domain) 
    CONFIRM.send(relay, "comment", message, "mail/comment_confirm.msg", locals())
    return CONFIRMING


@route("comment-confirm-(id_number)@(host)", id_number="[a-z0-9]+")
def CONFIRMING(message, id_number=None, host=None):
    original = CONFIRM.verify('comment', message['from'], id_number)

    if original:
        # headers are already attached from START
        comment.defer_to_queue(original)
        msg = view.respond(locals(), "mail/comment_submitted.msg",
                           From="noreply@%(host)s",
                           To=original['from'],
                           Subject="Your comment has been posted.")

        relay.deliver(msg)

        return COMMENTING
    else:
        logging.debug("Invalid confirm from %s", message['from'])
        return CONFIRMING


@route("(user_id)-AT-(domain)-(post_name)-comment@(host)")
def COMMENTING(message, user_id=None, post_name=None, host=None, domain=None):
    comment.attach_headers(message, user_id, post_name, domain) 
    comment.defer_to_queue(message)
    original = message # keeps the template happy

    msg = view.respond(locals(), "mail/comment_submitted.msg",
                       From="noreply@%(host)s",
                       To=original['from'],
                       Subject="Your comment has been posted.")
    relay.deliver(msg)

    return COMMENTING



