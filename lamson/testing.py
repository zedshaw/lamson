"""
A bag of generally useful things when writing unit tests for your Lamson server.
The most important things are the spelling function and using the
TestConversation vs. RouterConversation to talk to your server.

The TestConversation will use the lamson.server.Relay you have configured to
talk to your actual running Lamson server.  Since by default Lamson reloads each
file you change it will work to run your tests.

However, this isn't that fast, doesn't give you coverage analysis, and doesn't
let you test the results.  For that you use RouterConversation to do the exact
same API (they should be interchangeable) but rather than talk to a running
server through the relay, it just runs all the messages through the router
directly. 

This is faster and will give you code coverage as well as make sure that all the
modules (not just your handlers) will get reloaded.

The spelling function will use PyEnchant to spell check a string.  If it finds
any errors it prints them out, and returns False.
"""


from lamson import server, utils, routing, mail
from lamson.queue import Queue
from nose.tools import assert_equal
import re
import logging

TEST_QUEUE = "run/queue"


def spelling(file_name, contents, language="en_US"):
    """
    You give it a file_name and the contents of that file and it tells you
    if it's spelled correctly.  The reason you give it contents is that you
    will typically run a template through the render process, so spelling 
    can't just load a file and check it.

    It assumes you have PyEnchant installed correctly and configured 
    in your config/testing.py file.  Use "lamson spell" to make sure it
    works right.
    """
    try:
        from enchant.checker import SpellChecker 
        from enchant.tokenize import EmailFilter, URLFilter 
    except:
        print "Failed to load PyEnchant.  Make sure it's installed and lamson spell works."
        return True

    failures = 0
    chkr = SpellChecker(language, filters=[EmailFilter, URLFilter]) 
    chkr.set_text(contents)
    for err in chkr:
        print "%s: %s \t %r" % (file_name, err.word, contents[err.wordpos-20:err.wordpos+20])
        failures += 1

    if failures:
        print "You have %d spelling errors in %s.  Run lamson spell.." % (failures, file_name)
        return False
    else:
        return True




def relay(hostname="127.0.0.1", port=8824):
    """Wires up a default relay on port 8824 (the default lamson log port)."""
    return server.Relay(hostname, port, debug=0)


def queue(queue_dir=TEST_QUEUE):
    """Creates a queue for you to analyze the results of a send, uses the
    TEST_QUEUE setting in settings.py if that exists, otherwise defaults to
    run/queue."""
    return Queue(queue_dir)


def clear_queue(queue_dir=TEST_QUEUE):
    """Clears the default test queue out, as created by lamson.testing.queue."""
    queue(queue_dir).clear()


def delivered(pattern, to_queue=None):
    """
    Checks that a message with that patter is delivered, and then returns it.

    It does this by searching through the queue directory and finding anything that
    matches the pattern regex.
    """
    inq = to_queue or queue()
    for key in inq.keys():
        msg = inq.get(key)
        if not msg:
            # no messages in the queue
            return False

        regp = re.compile(pattern)
        if regp.search(str(msg)):
            msg = inq.get(key)
            return msg

    # didn't find anything
    return False


class TestConversation(object):
    """
    Used to easily do conversations with an email server such that you
    send a message and then expect certain responses.
    """

    def __init__(self, relay_to_use, From, Subject):
        """
        This creates a set of default values for the conversation so that you
        can easily send most basic message.  Each method lets you override the
        Subject and Body when you send.
        """
        self.relay = relay_to_use
        self.From = From
        self.Subject = Subject

    def begin(self):
        """Clears out the queue and Router states so that you have a fresh start."""
        clear_queue()
        routing.Router.clear_states()

    def deliver(self, To, From, Subject, Body):
        """Delivers it to the relay."""
        self.relay.send(To, From, Subject, Body)

    def say(self, To, Body, expect=None, Subject=None):
        """
        Say something to To and expect a reply with a certain address.
        It returns the message expected or None.
        """
        msg = None

        self.deliver(To, self.From, Subject or self.Subject, Body)
        if expect:
            msg = delivered(expect)
            if not msg:
                print "MESSAGE IN QUEUE:"
                inq = queue()
                for key in inq.keys():
                    print "-----"
                    print inq.get(key)

            assert msg, "Expected %r when sending to %r with '%s:%s' message." % (expect, 
                                          To, self.Subject or Subject, Body)
        return msg

class RouterConversation(TestConversation):
    """
    An implementation of TestConversation that routes the messages
    internally to the Router, rather than connecting with a relay.
    Use it in tests that are not integration tests.
    """
    def __init__(self, From, Subject):
        self.From = From
        self.Subject = Subject

    def deliver(self, To, From, Subject, Body):
        """Overrides TestConversation.deliver to do it internally."""
        sample = mail.MailResponse(From=From, To=To, Subject=Subject, Body=Body)
        msg = mail.MailRequest('localhost', sample['From'], sample['To'], str(sample))
        routing.Router.deliver(msg)



def assert_in_state(module, To, From, state):
    """
    Makes sure a user is in a certain state for a certain user.
    Use these sparingly, since every time you change your handler you'll
    have to change up your tests.  It's better to focus on the interaction
    with your handler and expected outputs.
    """
    fake = {'to': To}
    state_key = routing.Router.state_key(module, fake)
    assert_equal(routing.Router.STATE_STORE.get(state_key, From), state)


