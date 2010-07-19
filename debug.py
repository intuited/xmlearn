"""Various debugging functions which may be useful in the future."""

# format functions originally developed for use with deboogie.iterdebug
# and used to debug iter_unique_child_tags
from pprint import pformat
path = lambda n: n.getroottree().getpath(n)
def formatnode(o):
    return '{0}  [{1}]'.format(o.tag, path(o))
def lformat(label, format=str):
    return lambda o: '##  {0}: {1}'.format(label, format(o))
def lformatnode(label):
    return lformat(label, formatnode)
def lformatnodetuple(label):
    def format(t):
        return pformat({label: map(formatnode, t)})
    return format
def lformatnodetagtuple(label):
    def format(t):
        return pformat({label: (formatnode(t[0]), t[1])})
    return format
