from nose.tools import *
from lamson import mail
from app.model import comment

def test_attach_headers():
    msg = mail.MailRequest('test_attach_headers', 'tester@localhost', 'test.blog@oneshotblog.com',
                           'Fake body.')

    comment.attach_headers(msg)
    for key in ['X-Post-Name', 'X-Post-User-ID', 'X-Post-Domain']:
        assert key in msg

