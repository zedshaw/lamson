from lamson import queue, server, mail
from nose.tools import *
import shutil
import os
from mock import *
import mailbox

USE_SAFE=False

def setup():
    if os.path.exists("run/big_queue"):
        shutil.rmtree("run/big_queue")

def teardown():
    setup()


def test_push():
    q = queue.Queue("run/queue", safe=USE_SAFE)
    q.clear()

    # the queue doesn't really care if its a request or response, as long
    # as the object answers to str(msg)
    msg = mail.MailResponse(To="test@localhost", From="test@localhost",
                              Subject="Test", Body="Test")
    key = q.push(msg)
    assert key, "Didn't get a key for test_get push."

    return q


def test_pop():
    q = test_push()
    key, msg = q.pop()

    assert key, "Didn't get a key for test_get push."
    assert msg, "Didn't get a message for key %r" % key

    assert msg['to'] == "test@localhost"
    assert msg['from'] == "test@localhost"
    assert msg['subject'] == "Test"
    assert msg.body() == "Test"

    assert q.count() == 0, "Queue should be empty."
    assert not q.pop()[0]


def test_get():
    q = test_push()
    msg = mail.MailResponse(To="test@localhost", From="test@localhost",
                              Subject="Test", Body="Test")
    key = q.push(str(msg))
    assert key, "Didn't get a key for test_get push."

    msg = q.get(key)
    assert msg, "Didn't get a message for key %r" % key

def test_remove():
    q = test_push()
    msg = mail.MailResponse(To="test@localhost", From="test@localhost",
                              Subject="Test", Body="Test")
    key = q.push(str(msg))
    assert key, "Didn't get a key for test_get push."
    assert q.count() == 2, "Wrong count %d should be 2" % q.count()

    q.remove(key)
    assert q.count() == 1, "Wrong count %d should be 1" % q.count()



def test_safe_maildir():
    global USE_SAFE
    USE_SAFE=True
    test_push()
    test_pop()
    test_get()
    test_remove()


def test_oversize_protections():
    # first just make an oversize limited queue
    overq = queue.Queue("run/queue", pop_limit=10)
    overq.clear()

    for i in range(5):
        overq.push("HELLO" * 100)

    assert_equal(overq.count(), 5)

    key, msg = overq.pop()

    assert not key and not msg, "Should get no messages."
    assert_equal(overq.count(), 0)

    # now make sure that oversize mail is moved to the overq
    setup()
    overq = queue.Queue("run/queue", pop_limit=10, oversize_dir="run/big_queue")
    moveq = queue.Queue("run/big_queue")

    for i in range(5):
        overq.push("HELLO" * 100)

    key, msg = overq.pop()

    assert not key and not msg, "Should get no messages."
    assert_equal(overq.count(), 0)
    assert_equal(moveq.count(), 5)

    moveq.clear()
    overq.clear()


@patch('os.stat', new=Mock())
@raises(mailbox.ExternalClashError)
def test_SafeMaildir_name_clash():
    try:
        shutil.rmtree("run/queue")
    except: pass
    sq = queue.SafeMaildir('run/queue')
    sq.add("TEST")

def raise_OSError(*x, **kw):
    err = OSError('Fail')
    err.errno = 0
    raise err

@patch('mailbox._create_carefully', new=Mock())
@raises(OSError)
def test_SafeMaildir_throws_errno_failure():
    setup()
    mailbox._create_carefully.side_effect = raise_OSError
    sq = queue.SafeMaildir('run/queue')
    sq.add("TEST")

@patch('os.stat', new=Mock())
@raises(OSError)
def test_SafeMaildir_reraise_weird_errno():
    try:
        shutil.rmtree("run/queue")
    except: pass

    os.stat.side_effect = raise_OSError
    sq = queue.SafeMaildir('run/queue')
    sq.add('TEST')

