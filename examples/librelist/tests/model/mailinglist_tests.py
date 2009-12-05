from nose.tools import *
from app.model.mailinglist import *
from email.utils import parseaddr
from webapp.librelist.models import MailingList, Subscription
from lamson.mail import MailRequest, MailResponse
from lamson.testing import *

user_full_address = '"Zed A. Shaw" <zedshaw@zedshaw.com>'
user_name, user_address = parseaddr(user_full_address)
list_name = "test.lists"


def setup():
    MailingList.objects.all().delete()
    Subscription.objects.all().delete()


def test_create_list():
    mlist = create_list(list_name)
    assert mlist
    mlist_found = find_list(list_name)
    assert mlist_found
    assert_equal(mlist.name, mlist_found.name)

    # make sure create doesn't do it more than once
    create_list(list_name)
    assert_equal(MailingList.objects.filter(name = list_name).count(), 1)
    delete_list(list_name)


def test_delete_list():
    delete_list(list_name)
    mlist = find_list(list_name)
    assert not mlist, "Found list: %s, should not." % mlist


def test_remove_all_subscriptions():
    test_add_subscriber()

    remove_all_subscriptions(user_full_address)
    subs = find_subscriptions(user_full_address)
    assert_equal(len(subs), 0)


def test_add_subscriber():
    remove_all_subscriptions(user_full_address)
    sub = add_subscriber(user_full_address, list_name)
    assert sub
    assert_equal(sub.subscriber_address, user_address)
    assert_equal(sub.subscriber_name, user_name)

    subs = find_subscriptions(user_full_address)
    assert_equal(len(subs), 1)


def test_remove_subscriber():
    test_add_subscriber()
    remove_subscriber(user_full_address, list_name)
    subs = find_subscriptions(user_full_address, list_name=list_name)
    assert_equal(len(subs), 0)


def test_post_message():
    for i in range(0,3):
        add_subscriber(user_full_address, list_name)

    sample = MailResponse(To=list_name + "@librelist.com",
                          From=user_full_address,
                          Subject="Test post message.",
                          Body="I am telling you guys you are wrong.")

    sample['Message-Id'] = '12313123123123123'

    msg = MailRequest("fakepeer", sample['from'], sample['to'], str(sample))
    post_message(relay(port=8825), msg, list_name, "librelist.com")


def test_disable_enable_all_subscriptions():
    test_add_subscriber()
    disable_all_subscriptions(user_address)
    assert not find_subscriptions(user_address)

    enable_all_subscriptions(user_address)
    assert find_subscriptions(user_address)

def test_similarily_named_lists():
    test_names = ['test.lists', 'tests.list', 'querylists', 'evil.named',
                 'shouldnot', 'teller.list']
    for name in test_names:
        create_list(name)

    similar = similar_named_lists(list_name)
    assert_equal(len(similar), 2)

    nothing = similar_named_lists("zed.shaw")
    assert not nothing

    similar = similar_named_lists('teler.list')
    assert_equal(len(similar), 1)


def test_craft_response_attachment():
    sample = MailResponse(To=list_name + "@librelist.com",
                          From=user_full_address,
                          Subject="Test message with attachments.",
                          Body="The body as one attachment.")

    sample.attach(filename="tests/model/mailinglist_tests.py",
                  content_type="text/plain",
                  disposition="attachment")

    sample['message-id'] = '123545666'

    im = sample.to_message()
    assert_equal(len([x for x in im.walk()]), 3)
    
    inmsg = MailRequest("fakepeer", None, None, str(sample))
    assert_equal(len(inmsg.all_parts()), 2)

    outmsg = craft_response(inmsg, list_name, list_name +
                                        "@librelist.com")
  
    om = outmsg.to_message()

    assert_equal(len([x for x in om.walk()]),
                 len([x for x in im.walk()]))

    assert 'message-id' in outmsg


def test_craft_response_no_attachment():
    sample = MailResponse(To=list_name + "@librelist.com",
                          From=user_full_address,
                          Subject="Test message with attachments.",
                          Body="The body as one attachment.")

    im = sample.to_message()
    assert_equal(len([x for x in im.walk()]), 1)
    assert_equal(im.get_payload(), sample.Body)
    
    inmsg = MailRequest("fakepeer", None, None, str(sample))
    assert_equal(len(inmsg.all_parts()), 0)
    assert_equal(inmsg.body(), sample.Body)

    outmsg = craft_response(inmsg, list_name, list_name +
                                        "@librelist.com")
  
    om = outmsg.to_message()
    assert_equal(om.get_payload(), sample.Body)

    assert_equal(len([x for x in om.walk()]),
                 len([x for x in im.walk()]))


