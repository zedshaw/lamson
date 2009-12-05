from nose.tools import *
from lamson.testing import *
import os
import time
import shutil

relay = relay(port=8823)
sender = "sender-%s@sender.com" % time.time()
host = "oneshotblog.com"
blog_id = int(time.time())
blog_address = "test.blog.%d@%s" % (blog_id, host)

client = RouterConversation(sender, 'Post Tests Subject')

def test_new_user_subscribes():
    client.begin()
    msg = client.say(blog_address, "I'd like a blog thanks.", 'confirm')
    client.say(msg['Reply-To'], 'Confirmed I am.', 'noreply')

def test_bad_user_tries_invalid_confirm():
    client.begin()
    client.say(blog_address, "I want to break in.", 'confirm')
    clear_queue()  # make sure no message is available

    # attacker does not have the above message
    client.say("confirm-11111111@" + host, 'Sneaky I am.')
    assert not delivered('noreply'), "Should not get a reply to a bad confirm." + str(msg)


def test_existing_user_posts():
    test_new_user_subscribes()

    client.say(blog_address, "This is my new page.", "noreply")

    expected_file = "app/data/posts/%s/%s.html" % (sender, 'test.blog.%s' % blog_id)
    assert os.path.exists(expected_file), "Should get an html."


def test_existing_user_posts_invalid_action():
    test_new_user_subscribes()
    clear_queue()

    client.say("test.blog.%s-unfuddleamick@" + host, 'Please unfuddleamick me.')
    assert not delivered('noreply'), "Should get nothing for an invalid action."

def test_existing_user_deletes():
    test_new_user_subscribes()
    clear_queue()

    expected_file = "app/data/posts/%s/%s.html" % (sender, 'test.blog.%s' % blog_id)

    blog_delete = "test.blog.%s-delete@%s" % (blog_id, host)
    client.say(blog_delete, "Please delete.", "noreply")

    assert not os.path.exists(expected_file), "File should be gone."



