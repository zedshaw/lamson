from lamson.routing import *

@state_key_generator
def simple_key_gen(module_name, message):
    return module_name

# common routing capture regexes go in here, you can override them in @route
Router.defaults(host="localhost", 
                action="[a-zA-Z0-9]+",
                list_name="[a-zA-Z.0-9]+")


@route("(list_name)-(action)@(host)")
def START(message, list_name=None, action=None, host=None):
    print "START", message, list_name, action, host
    if action == 'explode':
        print "EXPLODE!"
        raise RuntimeError("Exploded on purpose.")
    return CONFIRM
    
@route("(list_name)-confirm-(id_number)@(host)", id_number="[0-9]+")
def CONFIRM(message, list_name=None, id_number=None, host=None):
    print "CONFIRM", message, list_name, id_number, host
    return POSTING

@route("(list_name)-(action)@(host)")
def POSTING(message, list_name=None, action=None, host=None):
    print "POSTING", message, list_name, action, host
    return NEXT

@route_like(POSTING)
def NEXT(message, list_name=None, action=None, host=None):
    print "NEXT", message, list_name, action, host
    return END

@route("(anything)@(host)", anything=".*")
def END(message, anything=None, host=None):
    print "END", anything, host
    return START

@route(".*")
@stateless
@nolocking
def PASSING(message, *args, **kw):
    print "PASSING", args, kw


try:
    @stateless
    @route("badstateless@(host)")
    def BAD_STATELESS(message, *args, **kw):
        print "BAD_STATELESS", args, kw
except AssertionError:
    pass  # we need to get this
