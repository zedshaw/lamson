from nose.tools import *
from lamson.testing import *
from lamson import mail
from config import settings
from app.model import addressing

user_real = 'zedshaw@zedshaw.com'
user_id = "user-%s" % addressing.random_id()
host = 'myinboxisnota.tv'

def test_store_lookup_delete():
    addressing.store(user_id, user_real)
    addr = addressing.lookup(user_id)
    assert_equal(addr, user_real)
   
    addressing.delete(user_id)
    assert_raises(KeyError, addressing.lookup, user_id)


def test_store_lookup_delete_with_dumb_addresses():
    addressing.store('"Zed Shaw" <zedshaw@zedshaw.com>', "fake")
    assert_equal("fake", addressing.lookup("zedshaw@zedshaw.com"))
    assert_equal("fake", addressing.lookup('"Zed Shaw" <zedshaw@zedshaw.com>'))
    addressing.delete("zedshaw@zedshaw.com")
    assert_raises(KeyError, addressing.lookup, "zedshaw@zedshaw.com")
    assert_raises(KeyError, addressing.lookup,'"Zed Shaw" <zedshaw@zedshaw.com>')

def test_random_id():
    id_number = addressing.random_id()
    assert id_number

def test_real():
    addressing.store(user_id, user_real)
    assert_equal(addressing.real(user_id), user_real)
    addressing.delete(user_id)


def test_anon():
    addressing.store(user_real, user_id)

    user_anon = addressing.anon(user_real, host)
    assert_equal(user_anon, user_id + '@' + host)

    addressing.delete(user_real)

def test_mapping():
    anon = addressing.mapping(user_real, 'user', host)
    anon_id = anon.split('@')[0]

    assert_equal(addressing.lookup(anon_id), user_real)
    assert_equal(addressing.lookup(user_real), anon_id)
    assert_equal(addressing.lookup(anon_id), user_real)

    addressing.delete(anon_id)
    addressing.delete(user_real)

