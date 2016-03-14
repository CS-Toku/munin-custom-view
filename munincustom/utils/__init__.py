
from collections import namedtuple

MachineTuple = namedtuple('MachineTuple', ['domain', 'host'])

def split_domainhost(dh):
    if ';' in dh:
        d, h = dh.split(';', 1)
    else:
        d, h = dh, dh

    return MachineTuple(d, h if h else None)
