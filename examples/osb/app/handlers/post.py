from app.model import post
from email.utils import parseaddr
from config.settings import relay, CONFIRM
from lamson import view, queue
from lamson.routing import route, stateless
import logging


@route("(post_name)@(host)")
def START(message, post_name=None, host=None):
    message['X-Post-Name'] = post_name

    CONFIRM.send(relay, "post", message, "mail/confirm.msg", locals())
    return CONFIRMING


@route("post-confirm-(id_number)@(host)", id_number="[a-z0-9]+")
def CONFIRMING(message, id_number=None, host=None):
    original = CONFIRM.verify('post', message['from'], id_number)

    if original:
        name, address = parseaddr(original['from'])
        post_name = original['x-post-name']

        post_id = post.post(post_name, address, host, original)
        msg = view.respond(locals(), "mail/welcome.msg",
                           From="noreply@%(host)s",
                           To=message['from'],
                           Subject="Welcome, your blog is ready.")
        relay.deliver(msg)

        return POSTING
    else:
        logging.warning("Invalid confirm from %s", message['from'])
        return CONFIRMING



@route("(post_name)@(host)")
@route("(post_name)-(action)@(host)", action="delete")
def POSTING(message, post_name=None, host=None, action=None):
    name, address = parseaddr(message['from'])

    if not action:
        post.post(post_name, address, host, message)
        msg = view.respond(locals(), 'mail/page_ready.msg', 
                           From="noreply@%(host)s",
                           To=message['from'],
                           Subject="Your page '%(post_name)s' is ready.")
        relay.deliver(msg)

        # first real message, now we can index it
        index_q = queue.Queue("run/posts")
        index_q.push(message)
    elif action == "delete":
        post.delete(post_name, address)

        msg = view.respond(locals(), 'mail/deleted.msg', 
                           From="noreply@%(host)s",
                           To=message['from'],
                           Subject="Your page '%(post_name)s' was deleted.")

        relay.deliver(msg)
    else:
        logging.debug("Invalid action: %r", action)

    return POSTING



