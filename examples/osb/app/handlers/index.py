from __future__ import with_statement
from email.utils import parseaddr
from lamson import view, queue
from lamson.routing import route, stateless
import logging
from config import settings
from app.model import post
from markdown import markdown



@route("(post_name)@(host)")
@stateless
def POSTING(message, post_name=None, host=None):
    user, address = parseaddr(message['from'])
    user = user or address
    post_url = "posts/%s/%s.html" % (address, post_name)

    index_q = queue.Queue("run/indexed")
    post_keys = sorted(index_q.keys(), reverse=True)
    old_keys = post_keys[50:]
    del post_keys[50:]

    # find the old one and remove it
    posts = []
    for key in post_keys:
        msg = index_q.get(key)
        if msg['x-post-url'] == post_url:
            # this is the old one, take it out
            index_q.remove(key)
        else:
            posts.append(msg)

    # update the index and our posts
    message['X-Post-URL'] = post_url
    index_q.push(message)
    posts.insert(0, message)

    # and generate the index with what we got now
    index = view.render(locals(), "web/index.html")

    f = open("app/data/index.html", "w")
    f.write(index.encode("utf-8"))
    f.close()

    # finally, zap all the old keys
    for old in old_keys: index_q.remove(old)


@route("(user_id)-AT-(domain)-(post_name)-comment@(host)")
@stateless
def COMMENTING(message, user_id=None, domain=None, post_name=None, host=None):
    address = user_id + '@' + domain
    user_dir = post.get_user_dir(address)

    if post.user_exists(address):
        # stuff it here for now, but we'll just build the file rolling
        comments = queue.Queue("%s/comments" % user_dir)
        comments.push(message)
        
        contents = markdown(message.body())
        comment_file = "%s/%s-comments.html" % (user_dir, post_name)
        snippet = view.render(locals(), "web/comments.html")
        with open(comment_file, "a") as out:
            out.write(snippet)

    else:
        logging.warning("Attempt to post to user %r but user doesn't exist.", address)

