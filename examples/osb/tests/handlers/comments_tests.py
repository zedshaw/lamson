from nose.tools import *
from lamson.testing import *
from lamson.routing import Router
from app.model import post
import time

sender = "sender-%s@localhost" % time.time()
host = "oneshotblog.com"
comment_id = int(time.time())
comment_address = "tester-AT-localhost-test.blog.%d-comment@%s" % (comment_id, host)
target_user = "tester@localhost"
sender = "commenter-%s@localhost" % time.time()
client = RouterConversation(sender, 'Comment Tests Subject')

def setup():
    clear_queue("run/posts")
    clear_queue("run/spam")
    post.make_user_dir(target_user)

def make_spam():
    spam_data = open("tests/spam").read()
    spam = mail.MailRequest("test_spam_sent_by_unconfirmed_user", "spammer@spamtime.com", "spam" + comment_address, spam_data)
    spam['To'] = "spam" + comment_address
    return spam

def test_new_user_comments():
    client.begin()
    msg = client.say(comment_address, "I totally disagree with you!", 'confirm')
    client.say(msg['Reply-To'], 'Confirmed I am.', 'noreply')
    assert delivered(sender, to_queue=queue("run/posts"))
    assert delivered(sender, to_queue=queue(post.get_user_dir(target_user) + "/comments"))


def test_confirmed_user_comments():
    test_new_user_comments()
    client.say(comment_address, "I said I disagree!", "noreply")
    assert delivered(sender, to_queue=queue("run/posts"))

def test_invalid_confirmation():
    client.begin()
    client.say(comment_address, "I want to break in.", 'confirm')
    clear_queue()  # make sure no message is available

    # attacker does not have the above message
    client.say("confirm-11111111@" + host, 'Sneaky I am.')
    assert not delivered('noreply'), "Should not get a reply to a bad confirm." + str(msg)

def test_spam_sent_by_unconfirmed_user():
    setup()

    client.begin()
    Router.deliver(make_spam())

def test_spam_sent_by_confirmed_user():
    test_confirmed_user_comments()
    clear_queue("run/posts")

    Router.deliver(make_spam())


