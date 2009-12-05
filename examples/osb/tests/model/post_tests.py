from nose.tools import *
from lamson.mail import MailRequest
from lamson import view
import os
import time
from app.model import post
import jinja2
import config
import shutil

view.LOADER = jinja2.Environment(loader=jinja2.PackageLoader('app', 'templates'))
user = "test_user@localhost"
blog = "test_blog"
name = "Tester Joe"

def test_post():
    message = MailRequest("fakepeer", user,
                          "%s@oneshotblog.com" % blog, "Fake body")
    message['Subject'] = 'Test subject'

    post.post(blog, user, "localhost", message)

    assert post.user_exists(user), "User dir not created."
    assert os.path.exists(post.blog_file_name(blog, user)), "File not made."

def test_delete():
    test_post()
    post.delete(blog, user)
    assert post.user_exists(user), "User dir should stay."
    assert not os.path.exists(post.blog_file_name(blog, user)), "File should go."

def test_make_user_dir():
    assert not os.path.exists("sampleuser")
    dir = post.make_user_dir("sampleuser")
    assert dir == post.get_user_dir("sampleuser")
    assert os.path.exists(dir)
    shutil.rmtree(dir)


def test_remove_from_queue():
    message = MailRequest("fakepeer", user,
                          "%s@oneshotblog.com" % blog, "Fake body")
    message['Subject'] = 'Test subject'

    post_q = post.get_user_post_queue(post.get_user_dir(user))

    post.post(blog, user, 'localhost', message)

    assert post_q.count(), "No messages in the post queue."
    count = post_q.count()

    post.remove_from_queue(blog, user)
    assert post_q.count() == count-1, "It didn't get removed."

def test_user_exists():
    assert post.user_exists(user)
    assert not post.user_exists(user + "nothere")

def test_get_user_dir():
    dir = post.get_user_dir(user)
    assert dir.startswith(config.settings.BLOG_BASE)
    assert dir.endswith(user)

def test_blog_file_name():
    name = post.blog_file_name(blog, user)
    assert name.endswith("html")


