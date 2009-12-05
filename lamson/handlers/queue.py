"""
Implements a handler that puts every message it receives into 
the run/queue directory.  It is intended as a debug tool so you
can inspect messages the server is receiving using mutt or 
the lamson queue command.
"""

from lamson.routing import route_like, stateless, nolocking
from lamson import queue, handlers
import logging

@route_like(handlers.log.START)
@stateless
@nolocking
def START(message, to=None, host=None):
    """
    @stateless and routes however handlers.log.START routes (everything).
    Has @nolocking, but that's alright since it's just writing to a maildir.
    """
    q = queue.Queue('run/queue')
    q.push(message)

