from config import settings
from lamson.routing import Router
from lamson.server import Relay, QueueReceiver
from lamson import view
import logging
import logging.config
import jinja2

# configure logging to go to a log file
logging.config.fileConfig("config/logging.conf")

# the relay host to actually send the final message to
settings.relay = Relay(host=settings.relay_config['host'], 
                       port=settings.relay_config['port'], debug=1)

# where to listen for incoming messages
settings.receiver = QueueReceiver('run/undeliverable', settings.queue_config['sleep'])

Router.defaults(**settings.router_defaults)
Router.load(['lamson.handlers.forward'])
Router.RELOAD=True
Router.UNDELIVERABLE_QUEUE=None

view.LOADER = jinja2.Environment(
    loader=jinja2.PackageLoader(settings.template_config['dir'], 
                                settings.template_config['module']))

