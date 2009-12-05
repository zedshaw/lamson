from nose.tools import *
from lamson import mail
from lamson.routing import Router


def test_bounce_analyzer_on_bounce():
    bm = mail.MailRequest(None,None,None, open("tests/bounce.msg").read())
    assert bm.is_bounce()
    assert bm.bounce
    assert bm.bounce.score == 1.0
    assert bm.bounce.probable()
    assert_equal(bm.bounce.primary_status, (5, u'Permanent Failure'))
    assert_equal(bm.bounce.secondary_status, (1, u'Addressing Status'))
    assert_equal(bm.bounce.combined_status, (11, u'Bad destination mailbox address'))

    assert bm.bounce.is_hard()
    assert_equal(bm.bounce.is_hard(), not bm.bounce.is_soft())

    assert_equal(bm.bounce.remote_mta, u'gmail-smtp-in.l.google.com')
    assert_equal(bm.bounce.reporting_mta, u'mail.zedshaw.com')
    assert_equal(bm.bounce.final_recipient,
                 u'asdfasdfasdfasdfasdfasdfewrqertrtyrthsfgdfgadfqeadvxzvz@gmail.com')
    assert_equal(bm.bounce.diagnostic_codes[0], u'550-5.1.1')
    assert_equal(bm.bounce.action, 'failed')
    assert 'Content-Description-Parts' in bm.bounce.headers

    assert bm.bounce.error_for_humans()

def test_bounce_analyzer_on_regular():
    bm = mail.MailRequest(None,None,None, open("tests/signed.msg").read())
    assert not bm.is_bounce()
    assert bm.bounce
    assert bm.bounce.score == 0.0
    assert not bm.bounce.probable()
    assert_equal(bm.bounce.primary_status, (None, None))
    assert_equal(bm.bounce.secondary_status, (None, None))
    assert_equal(bm.bounce.combined_status, (None, None))

    assert not bm.bounce.is_hard()
    assert not bm.bounce.is_soft()

    assert_equal(bm.bounce.remote_mta, None)
    assert_equal(bm.bounce.reporting_mta, None)
    assert_equal(bm.bounce.final_recipient, None)
    assert_equal(bm.bounce.diagnostic_codes, [None, None])
    assert_equal(bm.bounce.action, None)


def test_bounce_to_decorator():
    import bounce_filtered_mod
    msg = mail.MailRequest(None,None,None, open("tests/bounce.msg").read())

    Router.deliver(msg)
    assert Router.in_state(bounce_filtered_mod.START, msg)
    assert bounce_filtered_mod.HARD_RAN, "Hard bounce state didn't actually run: %r" % msg.route_to

    msg.bounce.primary_status = (4, u'Persistent Transient Failure')
    Router.clear_states()
    Router.deliver(msg)
    assert Router.in_state(bounce_filtered_mod.START, msg)
    assert bounce_filtered_mod.SOFT_RAN, "Soft bounce didn't actually run."

    msg = mail.MailRequest(None, None, None, open("tests/signed.msg").read())
    Router.clear_states()
    Router.deliver(msg)
    assert Router.in_state(bounce_filtered_mod.END, msg), "Regular messages aren't delivering."


def test_bounce_getting_original():
    msg = mail.MailRequest(None,None,None, open("tests/bounce.msg").read())
    msg.is_bounce()

    assert msg.bounce.notification
    assert msg.bounce.notification.body

    assert msg.bounce.report

    for part in msg.bounce.report:
        assert [(k,part[k]) for k in part]
        # these are usually empty, but might not be.  they are in our test
        assert not part.body

    assert msg.bounce.original
    assert_equal(msg.bounce.original['to'], msg.bounce.final_recipient)
    assert msg.bounce.original.body


def test_bounce_no_headers_error_message():
    msg = mail.MailRequest(None, None, None, "Nothing")
    msg.is_bounce()
    assert_equal(msg.bounce.error_for_humans(), 'No status codes found in bounce message.')

