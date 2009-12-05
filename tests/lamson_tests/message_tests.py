# Copyright (C) 2008 Zed A. Shaw.  Licensed under the terms of the GPLv3.

import warnings
from nose.tools import *
import re
import os
from lamson import mail, encoding
import email

sample_message = """From: somedude@localhost
To: somedude@localhost

Test
"""

def test_mail_request():
    # try with a half-assed message
    msg = mail.MailRequest("localhost", "zedfrom@localhost",
                           "zedto@localhost", "Fake body.")
    assert msg['to'] == "zedto@localhost", "To is %r" % msg['to']
    assert msg['from'] == "zedfrom@localhost", "From is %r" % msg['from']

    msg = mail.MailRequest("localhost", "somedude@localhost",
                             ["somedude@localhost"], sample_message)
    assert msg.original == sample_message

    assert_equal(msg['From'], "somedude@localhost")

    assert("From" in msg)
    del msg["From"]
    assert("From" not in msg)

    msg["From"] = "nobody@localhost"
    assert("From" in msg)
    assert_equal(msg["From"], "nobody@localhost")

    # validate that upper and lower case work for headers
    assert("FroM" in msg)
    assert("from" in msg)
    assert("From" in msg)
    assert_equal(msg['From'], msg['fRom'])
    assert_equal(msg['From'], msg['from'])
    assert_equal(msg['from'], msg['fRom'])

    # make sure repr runs
    print repr(msg)

    return msg

def test_mail_response_plain_text():
    sample = mail.MailResponse(To="receiver@localhost", 
                                 Subject="Test message",
                                 From="sender@localhost",
                                 Body="Test from test_mail_response_plain_text.")
    return sample

def test_mail_response_html():
    sample = mail.MailResponse(To="receiver@localhost", 
                                 Subject="Test message",
                                 From="sender@localhost",
                                 Html="<html><body><p>From test_mail_response_html</p></body></html>")
    return sample

def test_mail_response_html_and_plain_text():
    sample = mail.MailResponse(To="receiver@localhost", 
                                 Subject="Test message",
                                 From="sender@localhost",
                                 Html="<html><body><p>Hi there.</p></body></html>",
                                 Body="Test from test_mail_response_html_and_plain_text.")
    return sample

def test_mail_response_attachments():
    sample = mail.MailResponse(To="receiver@localhost", 
                                 Subject="Test message",
                                 From="sender@localhost",
                                 Body="Test from test_mail_response_attachments.")
    readme_data = open("./README").read()

    assert_raises(AssertionError, sample.attach, filename="./README", disposition="inline")

    sample.attach(filename="./README", content_type="text/plain", disposition="inline")
    assert len(sample.attachments) == 1
    assert sample.multipart

    msg = sample.to_message()
    assert_equal(len(msg.get_payload()), 2)

    sample.clear()
    assert len(sample.attachments) == 0
    assert not sample.multipart

    sample.attach(data=readme_data, filename="./README", content_type="text/plain")

    msg = sample.to_message()
    assert_equal(len(msg.get_payload()), 2)
    sample.clear()

    sample.attach(data=readme_data, content_type="text/plain")
    msg = sample.to_message()
    assert_equal(len(msg.get_payload()), 2)

    return sample


def test_mail_request_attachments():
    sample = test_mail_response_attachments()
    data = str(sample)

    msg = mail.MailRequest("localhost", None, None, data)

    msg_parts = msg.all_parts()
    sample_parts = sample.all_parts()

    readme = open("./README").read()

    # BUG: Python's MIME text attachment decoding drops trailing newline chars

    assert msg_parts[0].body == sample_parts[0].body
    # python drops chars at the end, so can't compare equally
    assert readme.startswith(msg_parts[1].body)
    assert msg.body() == sample_parts[0].body

    # test that we get at least one message for messages without attachments
    sample = test_mail_response_plain_text()
    msg = mail.MailRequest("localhost", None, None, str(sample))
    msg_parts = msg.all_parts()
    assert len(msg_parts) == 0, "Length is %d should be 0." % len(msg_parts)
    assert msg.body()


def test_mail_response_mailing_list_headers():
    list_addr = "test.users@localhost"

    msg = mail.MailResponse(From='somedude@localhost', To=list_addr, 
            Subject='subject', Body="Mailing list reply.")

    print repr(msg)

    msg["Sender"] = list_addr
    msg["Reply-To"] = list_addr
    msg["List-Id"] = list_addr
    msg["Return-Path"] = list_addr
    msg["In-Reply-To"] = 'Message-Id-1231123'
    msg["References"] = 'Message-Id-838845854'
    msg["Precedence"] = 'list'

    data = str(msg)

    req = mail.MailRequest('localhost', 'somedude@localhost', list_addr, data)

    headers = ['Sender', 'Reply-To', 'List-Id', 'Return-Path', 
               'In-Reply-To', 'References', 'Precedence']
    for header in headers:
        assert msg[header] == req[header]

    # try a delete
    del msg['Precedence']

def test_mail_response_ignore_case_headers():
    msg = test_mail_response_plain_text()
    # validate that upper and lower case work for headers
    assert("FroM" in msg)
    assert("from" in msg)
    assert("From" in msg)
    assert_equal(msg['From'], msg['fRom'])
    assert_equal(msg['From'], msg['from'])
    assert_equal(msg['from'], msg['fRom'])


def test_walk():
    bm = mail.MailRequest(None,None,None, open("tests/bounce.msg").read())
    parts = [x for x in bm.walk()]

    assert parts
    assert_equal(len(parts), 6)


def test_copy_parts():
    bm = mail.MailRequest(None,None,None, open("tests/bounce.msg").read())
    
    resp = mail.MailResponse(To=bm['to'], From=bm['from'],
                             Subject=bm['subject'])

    resp.attach_all_parts(bm)

    resp = resp.to_message()
    bm = bm.to_message()

    assert_equal(len([x for x in bm.walk()]), len([x for x in resp.walk()]))

   
def test_craft_from_sample():
    list_name = "test.list"
    user_full_address = "tester@localhost"

    sample = mail.MailResponse(To=list_name + "@localhost",
                          From=user_full_address,
                          Subject="Test message with attachments.",
                          Body="The body as one attachment.")
    sample.update({"Test": "update"})

    sample.attach(filename="tests/lamson_tests/message_tests.py",
                  content_type="text/plain",
                  disposition="attachment")
    
    inmsg = mail.MailRequest("fakepeer", None, None, str(sample))
    assert "Test" in sample.keys()

    for part in inmsg.to_message().walk():
        assert part.get_payload(), "inmsg busted."

    outmsg = mail.MailResponse(To=inmsg['from'], 
                          From=inmsg['to'],
                          Subject=inmsg['subject'])

    outmsg.attach_all_parts(inmsg)

    result = outmsg.to_message()

    for part in result.walk():
        assert part.get_payload(), "outmsg parts don't have payload."


def test_route_to_from_works():
    msg = mail.MailRequest("fakepeer", "from@localhost",
                                   [u"<to1@localhost>", u"to2@localhost"], "")
    assert '<' not in msg.route_to, msg.route_to

    msg = mail.MailRequest("fakepeer", "from@localhost",
                                   [u"to1@localhost", u"to2@localhost"], "")
    assert '<' not in msg.route_to, msg.route_to
    
    msg = mail.MailRequest("fakepeer", "from@localhost",
                                   [u"to1@localhost", u"<to2@localhost>"], "")
    assert '<' not in msg.route_to, msg.route_to

    msg = mail.MailRequest("fakepeer", "from@localhost",
                                   [u"to1@localhost"], "")
    assert '<' not in msg.route_to, msg.route_to

    msg = mail.MailRequest("fakepeer", "from@localhost",
                                   [u"<to1@localhost>"], "")
    assert '<' not in msg.route_to, msg.route_to


def test_decode_header_randomness():
    assert_equal(mail._decode_header_randomness(None), set())
    assert_equal(mail._decode_header_randomness(["z@localhost", '"Z A" <z@localhost>']), 
                 set(["z@localhost", "z@localhost"]))
    assert_equal(mail._decode_header_randomness("z@localhost"),
                 set(["z@localhost"]))
    assert_raises(encoding.EncodingError, mail._decode_header_randomness, 1)


def test_msg_is_deprecated():
    warnings.simplefilter("ignore")
    msg = mail.MailRequest(None, None, None, "")
    assert_equal(msg.msg, msg.base)
    resp = mail.MailResponse()
    assert_equal(resp.msg, resp.base)

