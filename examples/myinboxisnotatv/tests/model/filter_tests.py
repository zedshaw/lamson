from nose.tools import *
from lamson.testing import *
from lamson import mail
from config import settings
from app.model import filter, addressing


host = 'myinboxisnota.tv'
user = 'joe@leavemealone.com'
user_anon_addr = addressing.mapping(user, 'user', host)
marketroid = 'marketroid@buymycrap.com'
mk_anon_addr = addressing.mapping(marketroid, 'marketroid', host)
user_id = user_anon_addr.split('@')[0]
marketroid_id = mk_anon_addr.split('@')[0]


from_marketroid = mail.MailResponse(From=marketroid, To=user_anon_addr, Subject="Buy my crap!",
                                    Html="<html></body>You should buy this!</body></html>")
from_user = mail.MailResponse(From=user, To=mk_anon_addr, Subject="No thanks.",
                              Body="Sorry but I'd rather not.")


def setup():
    addressing.store(user_id, user)
    addressing.store(marketroid_id, marketroid)
    addressing.store(marketroid, marketroid_id)

def teardown():
    addressing.delete(user_id)
    addressing.delete(marketroid_id)
    addressing.delete(marketroid)


def test_craft_response():
    # message from marketroid to the user_anon_addr
    msg = mail.MailRequest('fakepeer', from_marketroid['from'],
                           from_marketroid['to'], str(from_marketroid))
    
    # the mail a user would need to respond to
    resp = filter.craft_response(msg, msg['From'], user,
                                 mk_anon_addr).to_message()

    assert_equal(resp['from'], marketroid)
    assert_equal(resp['to'], user)
    assert_equal(resp['reply-to'], mk_anon_addr)

    msg = mail.MailRequest('fakepeer', from_user['from'], from_user['to'],
                           str(from_user))

    # the mail a marketroid could respond to
    resp = filter.craft_response(msg, user_anon_addr, marketroid).to_message()
    assert_equal(resp['from'], user_anon_addr)
    assert_equal(resp['to'], marketroid)

    # make sure the user's address is never in a header
    for k,v in resp.items():
        assert_not_equal(resp[k], user)


def test_cleanse_incoming():
    msg = mail.MailRequest('fakepeer', from_marketroid['from'],
                           from_marketroid['to'], str(from_marketroid))

    reply = filter.cleanse_incoming(msg, user_id, host).to_message()
    assert_equal(reply['from'], marketroid)
    assert_equal(reply['to'], user)
    assert_equal(reply['reply-to'], mk_anon_addr)


def test_route_reply():
    msg = mail.MailRequest('fakepeer', from_user['from'], from_user['to'],
                           str(from_user))
    reply = filter.route_reply(msg, marketroid_id, host).to_message()

    # make sure the user's address is never in a header
    for k,v in reply.items():
        assert_not_equal(reply[k], user)


