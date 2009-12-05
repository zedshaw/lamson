from nose.tools import *
from lamson.testing import *
from lamson.mail import MailRequest, MailResponse
from app.model.confirmation import DjangoConfirmStorage
from mock import patch

user = "test_user@localhost"
list_name = "test_list_name"



def test_DjangoConfirmStorage():
    storage = DjangoConfirmStorage()
    storage.clear()

    storage.store(list_name, user, '123456', 'abcdefg')

    secret, pending_id = storage.get(list_name, user)
    assert_equal(secret, '123456')
    assert_equal(pending_id, 'abcdefg')

    storage.delete(list_name, user)

    secret, pending = storage.get(list_name, user)
    assert not secret
    assert not pending


