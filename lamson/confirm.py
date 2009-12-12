"""
Confirmation handling API that helps you get the whole confirm/pending/verify 
process correct.  It doesn't implement any handlers, but what it does do is
provide the logic for doing the following:

    * Take an email, put it in a "pending" queue, and then send out a confirm
    email with a strong random id.
    * Store the pending message ID and the random secret someplace for later
    verification.
    * Verify an incoming email against the expected ID, and get back the
    original.

You then just work this into your project's state flow, write your own
templates, and possibly write your own storage.
"""

import uuid
from lamson import queue, view
from email.utils import parseaddr

class ConfirmationStorage(object):
    """
    This is the basic confirmation storage.  For simple testing purposes
    you can just use the default hash db parameter.  If you do a deployment
    you can probably get away with a shelf hash instead.

    You can write your own version of this and use it.  The confirmation engine
    only cares that it gets something that supports all of these methods.
    """
    def __init__(self, db={}):
        """
        Change the db parameter to a shelf to get persistent storage.
        """
        self.confirmations = db

    def clear(self):
        """
        Used primarily in testing, this clears out all pending confirmations.
        """
        self.confirmations.clear()

    def key(self, target, from_address):
        """
        Used internally to construct a string key, if you write
        your own you don't need this.

        NOTE: To support proper equality and shelve storage, this encodes the
        key into ASCII.  Make a different subclass if you need unicode and your
        storage supports it.
        """
        key = target + ':' + from_address

        return key.encode('ascii')

    def get(self, target, from_address):
        """
        Given a target and a from address, this returns a tuple of (expected_secret, pending_message_id).
        If it doesn't find that target+from_address, then it should return a (None, None) tuple.
        """
        return self.confirmations.get(self.key(target, from_address), (None, None))

    def delete(self, target, from_address):
        """
        Removes a target+from_address from the storage.
        """
        try:
            del self.confirmations[self.key(target, from_address)]
        except KeyError:
            pass

    def store(self, target, from_address, expected_secret, pending_message_id):
        """
        Given a target, from_address it will store the expected_secret and pending_message_id
        of later verification.  The target should be a string indicating what is being
        confirmed.  Like "subscribe", "post", etc.

        When implementing your own you should *never* allow more than one target+from_address
        combination.
        """
        self.confirmations[self.key(target, from_address)] = (expected_secret,
                                                              pending_message_id)

class ConfirmationEngine(object):
    """
    The confirmation engine is what does the work of sending a confirmation, 
    and verifying that it was confirmed properly.  In order to use it you
    have to construct the ConfirmationEngine (usually in config/settings.py) and
    you write your confirmation message templates for sending.

    The primary methods you use are ConfirmationEngine.send and ConfirmationEngine.verify.
    """
    def __init__(self, pending_queue, storage):
        """
        The pending_queue should be a string with the path to the lamson.queue.Queue 
        that will store pending messages.  These messages are the originals the user
        sent when they tried to confirm.

        Storage should be something that is like ConfirmationStorage so that this
        can store things for later verification.
        """
        self.pending = queue.Queue(pending_queue)
        self.storage = storage

    def get_pending(self, pending_id):
        """
        Returns the pending message for the given ID.
        """
        return self.pending.get(pending_id)

    def push_pending(self, message):
        """
        Puts a pending message into the pending queue.
        """
        return self.pending.push(message)

    def delete_pending(self, pending_id):
        """
        Removes the pending message from the pending queue.
        """
        self.pending.remove(pending_id)


    def cancel(self, target, from_address, expect_secret):
        """
        Used to cancel a pending confirmation.
        """
        name, addr = parseaddr(from_address)

        secret, pending_id = self.storage.get(target, addr)

        if secret == expect_secret:
            self.storage.delete(target, addr)
            self.delete_pending(pending_id)

    def make_random_secret(self):
        """
        Generates a random uuid as the secret, in hex form.
        """
        return uuid.uuid4().hex

    def register(self, target, message):
        """
        Don't call this directly unless you know what you are doing.
        It does the job of registering the original message and the
        expected confirmation into the storage.
        """
        from_address = message.route_from

        pending_id = self.push_pending(message)
        secret = self.make_random_secret()
        self.storage.store(target, from_address, secret, pending_id)

        return "%s-confirm-%s" % (target, secret)

    def verify(self, target, from_address, expect_secret):
        """
        Given a target (i.e. "subscribe", "post", etc), a from_address
        of someone trying to confirm, and the secret they should use, this
        will try to verify their confirmation.  If the verify works then
        you'll get the original message back to do what you want with.

        If the verification fails then you are given None.

        The message is *not* deleted from the pending queue.  You can do
        that yourself with delete_pending.
        """
        assert expect_secret, "Must give an expected ID number."
        name, addr = parseaddr(from_address)

        secret, pending_id = self.storage.get(target, addr)

        if secret == expect_secret:
            self.storage.delete(target, addr)
            return self.get_pending(pending_id)
        else:
            return None

    def send(self, relay, target, message, template, vars):
        """
        This is the method you should use to send out confirmation messages.
        You give it the relay, a target (i.e. "subscribe"), the message they
        sent requesting the confirm, your confirmation template, and any
        vars that template needs.

        The result of calling this is that the template message gets sent through
        the relay, the original message is stored in the pending queue, and 
        data is put into the storage for later calls to verify.
        """
        confirm_address = self.register(target, message)
        vars.update(locals())
        msg = view.respond(vars, template, To=message['from'],
                           From="%(confirm_address)s@%(host)s",
                           Subject="Confirmation required")

        msg['Reply-To'] = "%(confirm_address)s@%(host)s" % vars

        relay.deliver(msg)

    def clear(self):
        """
        Used in testing to make sure there's nothing in the pending
        queue or storage.
        """
        self.pending.clear()
        self.storage.clear()
