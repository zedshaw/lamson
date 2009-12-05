"""
Uses the SpamBayes system to perform filtering and classification
of email.  It's designed so that you attach a single decorator
to the state functions you need to be "spam free", and then use the
lamson.spam.Filter code to do training.

SpamBayes comes with extensive command line tools for processing
maildir and mbox for spam.  A good way to train SpamBayes is to 
take mail that you know is spam and stuff it into a maildir, then
periodically use the SpamBayes tools to train from that.
"""

from functools import wraps
from lamson import queue
from spambayes import hammie, Options, storage
import os
import logging

class Filter(object):
    """
    This code implements simple filtering and is taken from the
    SpamBayes documentation.
    """
    def __init__(self, storage_file, config):
        options = Options.options
        options["Storage", "persistent_storage_file"] = storage_file
        options.merge_files(['/etc/hammierc', os.path.expanduser(config)])

        self.include_trained = Options.options["Headers", "include_trained"]
        self.dbname, self.usedb = storage.database_type([])

        self.mode = None
        self.h = None

        assert not Options.options["Hammie", "train_on_filter"], "Cannot train_on_filter."

    def open(self, mode):
        assert not self.h, "Cannot reopen, close first."
        assert not self.mode, "Mode should be None on open, bad state."
        assert mode in ['r', 'c'], "Must give a valid mode: r, c."

        self.mode = mode
        self.h = hammie.open(self.dbname, self.usedb, self.mode)

    def close(self):
        if not self.h: return

        assert self.mode, "Mode was not set."
        assert self.mode in ['r','c'], "self.mode was not r or c. Bad state."

        if self.mode == 'c':
            self.h.store()
            self.h.close()

        self.h = None
        self.mode = None


    def filter(self, msg):
        self.open('r')
        result = self.h.filter(msg)
        self.close()
        return result

    def train_ham(self, msg):
        self.open('c')
        self.h.train_ham(msg, self.include_trained)
        self.close()

    def train_spam(self, msg):
        self.open('c')
        self.h.train_spam(msg, self.include_trained)
        self.close()

    def untrain_ham(self, msg):
        self.open('c')
        self.h.untrain_ham(msg)
        self.close()

    def untrain_spam(self, msg):
        self.open('c')
        self.h.untrain_spam(msg)
        self.close()




class spam_filter(object):
    """
    This is a decorator you attach to states that should be protected from spam.
    You use it by doing:

        @spam_filter(ham_db, rcfile, spam_dump_queue, next_state=SPAMMING)

    Where ham_db is the path to your hamdb configuration, rcfile is the 
    SpamBayes config, and spam_dump_queue is where this filter should
    dump spam it detects.

    The next_state argument is optional, defaulting to None, but if you use
    it then Lamson will transition that user into that state.  Use it to mark
    that address as a spammer and to ignore their emails or do something
    fancy with them.
    """

    def __init__(self, storage, config, spam_queue, next_state=None):
        self.storage = storage
        self.config = config
        self.spam_queue = spam_queue
        self.next_state = next_state
        assert self.next_state, "You must give next_state function."

        if not os.path.exists(self.storage):
            logging.warn("SPAM filter for %r does not have a valid storage path, it'll still run but won't do anything.",
                        (self.storage, self.config, self.spam_queue,
                         self.next_state.__name__))
            self.functioning = False
        else:
            self.functioning = True

    def __call__(self, fn):
        @wraps(fn)
        def category_wrapper(message, *args, **kw):
            if self.functioning:
                if self.spam(message.to_message()):
                    self.enqueue_as_spam(message.to_message())
                    return self.next_state
                else:
                    return fn(message, *args, **kw)
            else:
                return fn(message, *args, **kw)
        return category_wrapper

    def spam(self, message):
        """Determines if the message is spam or not."""
        spfilter = Filter(self.storage, self.config)
        spfilter.filter(message)

        if 'X-Spambayes-Classification' in message:
            return message['X-Spambayes-Classification'].startswith('spam')
        else:
            return False

    def enqueue_as_spam(self, message):
        """Drops the message into the configured spam queue."""
        outq = queue.Queue(self.spam_queue)
        outq.push(str(message))

