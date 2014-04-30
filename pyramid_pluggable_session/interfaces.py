from zope.interface import Interface

class IPlugSession(Interface):
    """ In interface that describes a pluggable session
    """

    def loads(session, request):
        """ This function given a ``session`` and ``request`` should using the
        ``session_id`` attribute of the ``session``

        This function should return either the opaque session information or None.
        """

    def dumps(session, request, session_data):
        """ This function given a ``session`` and ``request`` should using the
        ``_session_id`` attribute of the ``session`` write the session
        information, with the ``session_id`` being used as a unique identifier,
        any previously stored session data should overwritten. ``session_data``
        is an opaque object, it's contents are a serialised version of the
        session data.

        If ``session_data`` is None, the session may safely be removed.
        """
