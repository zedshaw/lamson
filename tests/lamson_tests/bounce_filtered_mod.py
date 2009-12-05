from lamson.routing import route, route_like
from lamson.bounce import bounce_to


SOFT_RAN=False
HARD_RAN=False

@route(".+")
def SOFT_BOUNCED(message):
    global SOFT_RAN
    SOFT_RAN=True
    # remember to transition back to START or the mailer daemon 
    # at that host will be put in a bad state
    return START

@route(".+")
def HARD_BOUNCED(message):
    global HARD_RAN
    HARD_RAN=True
    # remember to transition back to START or the mailer daemon 
    # at that host will be put in a bad state
    return START

@route("(anything)@(host)", anything=".+", host=".+")
@bounce_to(soft=SOFT_BOUNCED, hard=HARD_BOUNCED)
def START(message, **kw):
    return END

@route_like(START)
def END(message, *kw):
    pass


