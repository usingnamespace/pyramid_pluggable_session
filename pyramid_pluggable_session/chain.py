import logging
log = logging.getLogger(__name__)

from pyramid.settings import aslist

from zope.interface import implementer

from .interfaces import IPlugSession

@implementer(IPlugSession)
class _ChainSessionPlug(object):
    """ Chain based session

    This allows you to chain various session plugs, for example local memory,
    memcache, database and then file system. This way we can try fastests to
    slowest in order.
    """
    def __init__(self, plugs):
        self.plugs = plugs

    def loads(self, session, request):
        for plug in self.plugs:
            sdata = plug.loads(session, request)

            if sdata:
                return sdata


    def dumps(self, session, request, sess_data):
        for plug in self.plugs:
            plug.dumps(session, request, sess_data)

    def clear(self, session, request):
        for plug in self.plugs:
            plug.clear(session, request)


required_settings = [
        'pluggable_session.chain.plugs',
        ]

def ChainSessionPlug(config):
    for _require in required_settings:
        if _require not in config.registry.settings:
            raise RuntimeError(_require + ' needs to be set.')

    plugs = aslist(config.registry.settings['pluggable_session.chain.plugs'], flatten=False)

    dotted_plugs = []
    for plug in plugs:
        plug = config.maybe_dotted(plug)
        dotted_plugs.append(plug(config))


    return _ChainSessionPlug(dotted_plugs)

def includeme(config):
    config.registry.registerUtility(ChainSessionPlug(config), IPlugSession)


