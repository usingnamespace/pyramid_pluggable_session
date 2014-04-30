import logging
log = logging.getLogger(__name__)

from zope.interface import implementer

from .interfaces import IPlugSession

def MemorySessionPlug(config):
    log.warning("This session plug is not recommended for production.")
    storage = {}

    @implementer(IPlugSession)
    class _MemorySessionPlug(object):
        def loads(self, session, request):
            return storage.get(session._session_id, None)

        def dumps(self, session, request, sess_data):
            storage[session._session_id] = sess_data

        def clear(self, session, request):
            if session._session_id in storage:
                del storage[session._session_id]

    return _MemorySessionPlug()

def includeme(config):
    config.registry.registerUtility(MemorySessionPlug(config), IPlugSession)
