from nose.tools import *
from lamson.routing import Router
from lamson_tests import message_tests
import lamson.handlers.log
import lamson.handlers.queue

def test_log_handler():
    Router.deliver(message_tests.test_mail_request())

def test_queue_handler():
    Router.deliver(message_tests.test_mail_request())
