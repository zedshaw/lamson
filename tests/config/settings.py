# This file contains python variables that configure Lamson for email processing.
import logging

relay_config = {'host': 'localhost', 'port': 8825}

receiver_config = {'host': 'localhost', 'port': 8823}

handlers = []

router_defaults = {'host': 'localhost'}

template_config = {'dir': 'lamson_tests', 'module': '.'}

BLOG_BASE="app/data/posts"

# this is for when you run the config.queue boot
queue_config = {'queue': 'run/deferred', 'sleep': 10}

queue_handlers = []

