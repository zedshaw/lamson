"""
Simpler queue management than the regular mailbox.Maildir stuff.  You
do get a lot more features from the Python library, so if you need
to do some serious surgery go use that.  This works as a good
API for the 90% case of "put mail in, get mail out" queues.
"""

import mailbox
from lamson import mail
import hashlib
import socket
import time
import os
import errno
import logging

# we calculate this once, since the hostname shouldn't change for every
# email we put in a queue
HASHED_HOSTNAME = hashlib.md5(socket.gethostname()).hexdigest()

class SafeMaildir(mailbox.Maildir):
    def _create_tmp(self):
        now = time.time()
        uniq = "%s.M%sP%sQ%s.%s" % (int(now), int(now % 1 * 1e6), os.getpid(),
                                    mailbox.Maildir._count, HASHED_HOSTNAME)
        path = os.path.join(self._path, 'tmp', uniq)
        try:
            os.stat(path)
        except OSError, e:
            if e.errno == errno.ENOENT:
                mailbox.Maildir._count += 1
                try:
                    return mailbox._create_carefully(path)
                except OSError, e:
                    if e.errno != errno.EEXIST:
                        raise
            else:
                raise

        # Fall through to here if stat succeeded or open raised EEXIST.
        raise mailbox.ExternalClashError('Name clash prevented file creation: %s' % path)


class QueueError(Exception):

    def __init__(self, msg, data):
        Exception.__init__(self, msg)
        self._message = msg
        self.data = data


class Queue(object):
    """
    Provides a simplified API for dealing with 'queues' in Lamson.
    It currently just supports maildir queues since those are the 
    most robust, but could implement others later.
    """

    def __init__(self, queue_dir, safe=False, pop_limit=0, oversize_dir=None):
        """
        This gives the Maildir queue directory to use, and whether you want
        this Queue to use the SafeMaildir variant which hashes the hostname
        so you can expose it publicly.

        The pop_limit and oversize_queue both set a upper limit on the mail
        you pop out of the queue.  The size is checked before any Lamson
        processing is done and is based on the size of the file on disk.  The
        purpose is to prevent people from sending 10MB attachments.  If a
        message is over the pop_limit then it is placed into the
        oversize_dir (which should be a maildir).

        The oversize protection only works on pop messages off, not
        putting them in, get, or any other call.  If you use get you can
        use self.oversize to also check if it's oversize manually.
        """
        self.dir = queue_dir

        if safe:
            self.mbox = SafeMaildir(queue_dir)
        else:
            self.mbox = mailbox.Maildir(queue_dir)

        self.pop_limit = pop_limit

        if oversize_dir:
            if not os.path.exists(oversize_dir):
                osmb = mailbox.Maildir(oversize_dir)

            self.oversize_dir = os.path.join(oversize_dir, "new")

            if not os.path.exists(self.oversize_dir):
                os.mkdir(self.oversize_dir)
        else:
            self.oversize_dir = None

    def push(self, message):
        """
        Pushes the message onto the queue.  Remember the order is probably
        not maintained.  It returns the key that gets created.
        """
        return self.mbox.add(str(message))

    def pop(self):
        """
        Pops a message off the queue, order is not really maintained
        like a stack.

        It returns a (key, message) tuple for that item.
        """
        for key in self.mbox.iterkeys():
            over, over_name =  self.oversize(key)

            if over:
                if self.oversize_dir:
                    logging.info("Message key %s over size limit %d, moving to %s.",
                                key, self.pop_limit, self.oversize_dir)
                    os.rename(over_name, os.path.join(self.oversize_dir, key))
                else:
                    logging.info("Message key %s over size limit %d, DELETING (set oversize_dir).", 
                                key, self.pop_limit)
                    os.unlink(over_name)
            else:
                try:
                    msg = self.get(key)
                except QueueError, exc:
                    raise exc
                finally:
                    self.remove(key)
                return key, msg

        return None, None

    def get(self, key):
        """
        Get the specific message referenced by the key.  The message is NOT
        removed from the queue.
        """
        try:
            msg_file = self.mbox.get_file(key)
        except:
            logging.exception("Failed to get file, message gone?")
            return None

        if not msg_file: 
            return None

        msg_data = msg_file.read()

        try:
            return mail.MailRequest(self.dir, None, None, msg_data)
        except:
            logging.exception("Failed to decode message: msg_data: %r", msg_data)
            return None


    def remove(self, key):
        """Removes the queue, but not returned."""
        try:
            self.mbox.remove(key)
        except:
            logging.exception("Failed to remove message from queue.")
    
    def count(self):
        """Returns the number of messages in the queue."""
        return len(self.mbox)

    def clear(self):
        """
        Clears out the contents of the entire queue.
        Warning: This could be horribly inefficient since it
        basically pops until the queue is empty.
        """
        # man this is probably a really bad idea
        while self.count() > 0:
            self.pop()
    
    def keys(self):
        """
        Returns the keys in the queue.
        """
        return self.mbox.keys()

    def oversize(self, key):
        if self.pop_limit:
            file_name = os.path.join(self.dir, "new", key)
            return os.path.getsize(file_name) > self.pop_limit, file_name
        else:
            return False, None



