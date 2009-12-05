# This file contains python variables that configure Lamson for email processing.
import logging
import shelve
from lamson import confirm

relay_config = {'host': 'localhost', 'port': 8825}

receiver_config = {'host': 'localhost', 'port': 8823}

handlers = ['app.handlers.anonymizer']

router_defaults = {
    'host': 'myinboxisnota.tv',
    'user_id': 'user-[a-z0-9]+',
    'marketroid_id': 'marketroid-[a-z0-9]+',
    'id_number': '[a-z0-9]+',
}

template_config = {'dir': 'app', 'module': 'templates'}

SPAM = {'db': 'run/spamdb', 'rc': 'run/spamrc', 'queue': 'run/spam'}

BOUNCES = 'run/bounces'
UNDELIVERABLES = 'run/undeliverables'
CONFIRM_STORAGE=confirm.ConfirmationStorage(db=shelve.open("run/confirmationsdb"))

CONFIRM = confirm.ConfirmationEngine('run/pending', CONFIRM_STORAGE)
