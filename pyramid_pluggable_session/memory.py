import logging
log = logging.getLogger(__name__)

from zope.interface import implementer

from .interfaces import IPlugSession

_memory_storage = {}

@implementer(IPlugSession)
class MemorySessionPlug(object):
    def __init__(self):
        for i in xrange(10):
            log.warning("DO NOT USE THIS IN PRODUCTION SYSTEMS!")

    def loads(self, session, request):
        global _memory_storage

        try:
            return _memory_storage[session._session_id]
        except KeyError:
            return None

    def dumps(self, session, request, sess_data):
        global _memory_storage

        _memory_storage[session._session_id] = sess_data

def includeme(config):
    for i in xrange(10):
        log.warning("DO NOT USE THIS IN PRODUCTION SYSTEMS!")
    config.registry.registerUtility(MemorySessionPlug(), IPlugSession)
