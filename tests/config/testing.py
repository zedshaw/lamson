from config import settings
from lamson import view
from lamson.routing import Router
from lamson.server import Relay
import jinja2
import logging
import logging.config
import os

# configure logging to go to a log file
logging.config.fileConfig("tests/config/logging.conf")

# the relay host to actually send the final message to (set debug=1 to see what
# the relay is saying to the log server).
settings.relay = Relay(host=settings.relay_config['host'], 
                       port=settings.relay_config['port'], debug=0)


settings.receiver = None

Router.defaults(**settings.router_defaults)
Router.load(settings.handlers + settings.queue_handlers)
Router.RELOAD=False
Router.LOG_EXCEPTIONS=False

view.LOADER = jinja2.Environment(loader=jinja2.PackageLoader('lamson_tests', 'templates'))

# if you have pyenchant and enchant installed then the template tests will do
# spell checking for you, but you need to tell pyenchant where to find itself
if 'PYENCHANT_LIBRARY_PATH' not in os.environ:
    os.environ['PYENCHANT_LIBRARY_PATH'] = '/opt/local/lib/libenchant.dylib'

