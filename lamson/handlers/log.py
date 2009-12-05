"""
Implements a simple logging handler that's actually used by the lamson log
command line tool to run a logging server.  It simply takes every message it
receives and dumps it to the logging.debug stream.
"""

from lamson.routing import route, stateless
import logging

@route("(to)@(host)", to=".+", host=".+")
@stateless
def START(message, to=None, host=None):
    """This is stateless and handles every email no matter what, logging what it receives."""
    logging.debug("MESSAGE to %s@%s:\n%s" % (to, host, str(message)))


