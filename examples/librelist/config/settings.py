# This file contains python variables that configure Lamson for email processing.
import logging
import os
from lamson import confirm, encoding


encoding.VALUE_IS_EMAIL_ADDRESS = lambda v: '@' in v or '-AT-' in v


os.environ['DJANGO_SETTINGS_MODULE'] = 'webapp.settings'

relay_config = {'host': 'localhost', 'port': 8825}

receiver_config = {'host': 'localhost', 'port': 8823}

handlers = ['app.handlers.bounce', 'app.handlers.admin']

router_defaults = {
    'host': 'librelist\\.com',
    'list_name': '[a-zA-Z0-9\.]+',
    'id_number': '[a-z0-9]+',
}

template_config = {'dir': 'app', 'module': 'templates'}

# the config/boot.py will turn these values into variables set in settings

PENDING_QUEUE = "run/pending"
ARCHIVE_BASE = "app/data/archive"
BOUNCE_ARCHIVE = "run/bounces"

SPAM = {'db': 'run/spamdb', 'rc': 'run/spamrc', 'queue': 'run/spam'}

from app.model.confirmation import DjangoConfirmStorage
CONFIRM = confirm.ConfirmationEngine('run/pending', DjangoConfirmStorage())

