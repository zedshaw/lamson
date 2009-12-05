import os
import logging
from lamson import view, queue
import email
from config.settings import BLOG_BASE
from markdown import markdown


def delete(post_name, user):
    file_name = blog_file_name(post_name, user)

    if os.path.exists(file_name):
        logging.debug("DELETING %s", file_name)
        os.unlink(file_name)
        remove_from_queue(post_name, user)


def post(post_name, user, host, message):
    user_dir = make_user_dir(user)
    user_id, domain = user.split("@")

    # make sure it's removed first if it existed
    delete(post_name, user)

    posting = open("%s/%s.html" % (user_dir, post_name), "w")
    content = markdown(message.body())

    html = view.render(locals(), "web/post.html")

    posting.write(html.encode('utf-8'))

    post_q = get_user_post_queue(user_dir)
    post_q.push(message)


def make_user_dir(user):
    user_dir = get_user_dir(user)

    if not user_exists(user):
        os.mkdir(user_dir)

    return user_dir

def remove_from_queue(post_name, user):
    user_dir = get_user_dir(user)
    post_q = get_user_post_queue(user_dir)
    for k in post_q.keys():
        msg = post_q.get(k)
        name, address = email.utils.parseaddr(msg['to'])
        if address.startswith(post_name):
            logging.debug("Removing %s:%s from the queue", k, address)
            post_q.remove(k)


def user_exists(user):
    return os.path.exists(get_user_dir(user))

def get_user_dir(user):
    return "%s/%s" % (BLOG_BASE, user)

def blog_file_name(post_name, user):
    return "%s/%s.html" % (get_user_dir(user), post_name)

def get_user_post_queue(user_dir):
    queue_dir = "%s/posts_queue" % (user_dir)
    return queue.Queue(queue_dir)

