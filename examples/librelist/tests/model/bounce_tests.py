from nose.tools import *
from lamson.testing import *
from lamson.mail import MailRequest
from app.model import bounce


def test_mail_to_you_is_bouncing():
    msg = MailRequest("fakepeer", None, None, open("tests/bounce.msg").read())
    assert msg.is_bounce()

    bounce_rep = bounce.mail_to_you_is_bouncing(msg)
    assert bounce_rep
    assert_equal(bounce_rep['to'], msg.bounce.final_recipient)

