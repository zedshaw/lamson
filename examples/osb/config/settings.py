# This file contains python variables that configure Lamson for email processing.
from lamson import queue, routing, confirm
import logging
import shelve

relay_config = {'host': 'localhost', 'port': 8825}

receiver_config = {'host': 'localhost', 'port': 8823}

handlers = ['app.handlers.post', 'app.handlers.comment']

router_defaults = {'host': 'oneshotblog\\.com', 
                   'domain': "localhost|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}",
                   'user_id': "[a-zA-Z0-9._%+-]+",
                   'post_name': "[a-zA-Z0-9][a-zA-Z0-9.]+"}

template_config = {'dir': 'app', 'module': 'templates'}

BLOG_BASE="app/data/posts"

# this is for when you run the config.queue boot
queue_config = {'queue': 'run/posts', 'sleep': 10}

queue_handlers = ['app.handlers.index']

SPAM = {'db': 'app/spamdb', 'rc': 'spamrc', 'queue': 'run/spam'}

routing.Router.UNDELIVERABLE_QUEUE=queue.Queue("run/undeliverable")

CONFIRM_STORAGE=confirm.ConfirmationStorage(db=shelve.open("run/confirmationsdb"))
CONFIRM = confirm.ConfirmationEngine('run/pending', CONFIRM_STORAGE)

