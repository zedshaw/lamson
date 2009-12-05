from pytyrant import PyTyrant
import uuid
import zlib
from email.utils import parseaddr


def lookup(address, host=None):
    name, addr = parseaddr(address)
    table = PyTyrant.open()
    user = table[addr]
    table.close()

    if host:
        return user + '@' + host
    else:
        return user

def store(address, maps_to):
    name, addr = parseaddr(address)
    table = PyTyrant.open()
    table[addr] = maps_to
    table.close()

def delete(address):
    name, addr = parseaddr(address)
    table = PyTyrant.open()
    del table[addr]
    table.close()

def random_id():
    return "%x" % abs(zlib.adler32(uuid.uuid4().hex))


def mapping(real_address, anon_type, host):
    assert anon_type in ['user', 'marketroid']
    
    anon_id = "%s-%s" % (anon_type, random_id())

    store(anon_id, real_address)
    store(real_address, anon_id)

    return anon_id + '@' + host


def real(user_id):
    return lookup(user_id)


def anon(real, host):
    return lookup(real, host)



