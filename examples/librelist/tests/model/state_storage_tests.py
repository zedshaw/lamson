from nose.tools import *
from app.model.state_storage import UserStateStorage
from webapp.librelist.models import UserState
from lamson.routing import ROUTE_FIRST_STATE


def setup():
    for state in UserState.objects.all():
        state.delete()

def test_clear():
    ss = UserStateStorage()
    ss.clear()
    assert_equal(len(UserState.objects.all()), 0)


def test_set():
    ss = UserStateStorage()
    # start states should not be stored
    ss.set("app.handlers.admin", "zedshaw@zedshaw.com", "START")
    assert_equal(len(UserState.objects.all()), 0)

    ss.set("app.handlers.admin", "zedshaw@zedshaw.com", "POSTING")
    assert_equal(len(UserState.objects.all()), 1)
    
    ss.clear()

def test_get():
    ss = UserStateStorage()
    ss.clear()
    state = ss.get("app.handlers.admin", "zedshaw@zedshaw.com")
    assert_equal(state, ROUTE_FIRST_STATE)

    ss.set("app.handlers.admin", "zedshaw@zedshaw.com", "POSTING")
    state = ss.get("app.handlers.admin", "zedshaw@zedshaw.com")
    assert_equal(state, "POSTING")
