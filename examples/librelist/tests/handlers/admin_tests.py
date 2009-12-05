from nose.tools import *
from lamson.testing import *
from config import settings
import time
from app.model import archive, confirmation


queue_path = archive.store_path('test.list', 'queue')
sender = "sender-%s@sender.com" % time.time()
host = "librelist.com"
list_name = "test.list"
list_addr = "test.list@%s" % host
client = RouterConversation(sender, 'Admin Tests')

def setup():
    clear_queue("run/posts")
    clear_queue("run/spam")

def test_new_user_subscribes_with_invalid_name():
    client.begin()

    client.say('test-list@%s' % host, "I can't read!", 'noreply')
    client.say('test=list@%s' % host, "I can't read!", 'noreply')
    clear_queue()

    client.say('unbounce@%s' % host, "I have two email addresses!")
    assert not delivered('noreply')
    assert not delivered('unbounce')

    client.say('noreply@%s' % host, "Dumb dumb.")
    assert not delivered('noreply')

def test_new_user_subscribes():
    client.begin()
    msg = client.say(list_addr, "Hey I was wondering how to fix this?",
                     list_name + '-confirm')
    client.say(msg['Reply-To'], 'Confirmed I am.', 'noreply')
    clear_queue()


def test_existing_user_unsubscribes():
    test_new_user_subscribes()
    msg = client.say(list_name + "-unsubscribe@%s" % host, "I would like to unsubscribe.", 'confirm')
    client.say(msg['Reply-To'], 'Confirmed yes I want out.', 'noreply')

def test_existing_user_posts_message():
    test_new_user_subscribes()
    msg = client.say(list_addr, "Howdy folks, I was wondering what this is?",
                     list_addr)
    # make sure it gets archived
    assert delivered(list_addr, to_queue=queue(queue_path))


