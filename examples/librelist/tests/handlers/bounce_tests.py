from nose.tools import *
from lamson.testing import *
from lamson.mail import MailRequest
from lamson.routing import Router
from app.handlers.admin import module_and_to
from app.model import mailinglist
from handlers import admin_tests
from email.utils import parseaddr
from lamson import bounce
from config import settings

sender = admin_tests.sender
list_addr = admin_tests.list_addr
client = admin_tests.client

def setup():
    clear_queue(queue_dir=settings.BOUNCE_ARCHIVE)

def create_bounce(To, From):
    msg = MailRequest("fakepeer", From, To, open("tests/bounce.msg").read())
    assert msg.is_bounce()

    msg.bounce.final_recipient = From
    msg.bounce.headers['Final-Recipient'] = From
    msg.bounce.original['from'] = From
    msg.bounce.original['to'] = To
    msg.bounce.original.To = set([To])
    msg.bounce.original.From = From

    return msg


def test_hard_bounce_disables_user():
    # get them into a posting state
    admin_tests.test_existing_user_posts_message()
    assert_in_state('app.handlers.admin', list_addr, sender, 'POSTING')
    clear_queue()
    assert mailinglist.find_subscriptions(sender, list_addr)

    # force them to HARD bounce
    msg = create_bounce(list_addr, sender)

    Router.deliver(msg)
    assert_in_state('app.handlers.admin', list_addr, sender, 'BOUNCING')
    assert_in_state('app.handlers.bounce', list_addr, sender, 'BOUNCING')
    assert not delivered('unbounce'), "A HARD bounce should be silent."
    assert_equal(len(queue(queue_dir=settings.BOUNCE_ARCHIVE).keys()), 1)
    assert not mailinglist.find_subscriptions(sender, list_addr)

    # make sure that any attempts to post return a "you're bouncing dude" message
    unbounce = client.say(list_addr, 'So anyway as I was saying.', 'unbounce')
    assert_in_state('app.handlers.admin', list_addr, sender, 'BOUNCING')
   
    # now have them try to unbounce
    msg = client.say(unbounce['from'], "Please put me back on, I'll be good.",
                     'unbounce-confirm')

    # handle the bounce confirmation
    client.say(msg['from'], "Confirmed to unbounce.", 'noreply')

    # alright they should be in the unbounce state for the global bounce handler
    assert_in_state('app.handlers.bounce', list_addr, sender,
                    'UNBOUNCED')

    # and they need to be back to POSTING for regular operations 
    assert_in_state('app.handlers.admin', list_addr, sender, 'POSTING')
    assert mailinglist.find_subscriptions(sender, list_addr)

    # and make sure that only the original bounce is in the bounce archive
    assert_equal(len(queue(queue_dir=settings.BOUNCE_ARCHIVE).keys()), 1)

def test_soft_bounce_tells_them():
    setup()

    # get them into a posting state
    admin_tests.test_existing_user_posts_message()
    assert_in_state('app.handlers.admin', list_addr, sender, 'POSTING')
    clear_queue()
    assert mailinglist.find_subscriptions(sender, list_addr)

    # force them to soft bounce
    msg = create_bounce(list_addr, sender)
    msg.bounce.primary_status = (3, bounce.PRIMARY_STATUS_CODES[u'3'])
    assert msg.bounce.is_soft()

    Router.deliver(msg)
    assert_in_state('app.handlers.admin', list_addr, sender, 'BOUNCING')
    assert_in_state('app.handlers.bounce', list_addr, sender, 'BOUNCING')
    assert delivered('unbounce'), "Looks like unbounce didn't go out."
    assert_equal(len(queue(queue_dir=settings.BOUNCE_ARCHIVE).keys()), 1)
    assert not mailinglist.find_subscriptions(sender, list_addr)

    # make sure that any attempts to post return a "you're bouncing dude" message
    unbounce = client.say(list_addr, 'So anyway as I was saying.', 'unbounce')
    assert_in_state('app.handlers.admin', list_addr, sender, 'BOUNCING')

    # now have them try to unbounce
    msg = client.say(unbounce['from'], "Please put me back on, I'll be good.",
                     'unbounce-confirm')

    # handle the bounce confirmation
    client.say(msg['from'], "Confirmed to unbounce.", 'noreply')

    # alright they should be in the unbounce state for the global bounce handler
    assert_in_state('app.handlers.bounce', list_addr, sender,
                    'UNBOUNCED')

    # and they need to be back to POSTING for regular operations 
    assert_in_state('app.handlers.admin', list_addr, sender, 'POSTING')
    assert mailinglist.find_subscriptions(sender, list_addr)

    # and make sure that only the original bounce is in the bounce archive
    assert_equal(len(queue(queue_dir=settings.BOUNCE_ARCHIVE).keys()), 1)


