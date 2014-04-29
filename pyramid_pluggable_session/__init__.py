import base64
import binascii
import hashlib
import hmac
import os
import time

from webob.cookies import (
        SignedCookieProfile as CookieHelper,
        SignedSerializer,
        )

from zope.interface import implementer
from pyramid.interfaces import ISession

from pyramid.settings import (
        asbool,
        aslist,
        )

from pyramid.session import (
    manage_accessed,
    manage_changed,
    PickleSerializer,
    )

from pyramid.compat import (
    PY3,
    text_,
    bytes_,
    native_,
    )

from .interfaces import IPlugSession

# Most of this code was shamelessly lifted from pyramid/session.py, all
# original code is under the Pyramid LICENSE, modifications are under BSD

def PluggableSessionFactory(
    secret,
    cookie_name='session',
    max_age=None,
    path='/',
    domain=None,
    secure=False,
    httponly=False,
    set_on_exception=True,
    timeout=1200,
    reissue_time=0,
    hashalg='sha512',
    salt='pyramid_pluggable_session.',
    serializer=None,
    ):
    """
    .. versionadded:: 1.5

    Configure a :term:`session factory` which will provide signed
    cookie-based sessions.  The return value of this
    function is a :term:`session factory`, which may be provided as
    the ``session_factory`` argument of a
    :class:`pyramid.config.Configurator` constructor, or used
    as the ``session_factory`` argument of the
    :meth:`pyramid.config.Configurator.set_session_factory`
    method.

    The session factory returned by this function will create sessions
    which are limited to storing fewer than 4000 bytes of data (as the
    payload must fit into a single cookie).

    Parameters:

    ``secret``
      A string which is used to sign the cookie. The secret should be at
      least as long as the block size of the selected hash algorithm. For
      ``sha512`` this would mean a 128 bit (64 character) secret.  It should
      be unique within the set of secret values provided to Pyramid for
      its various subsystems (see :ref:`admonishment_against_secret_sharing`).

    ``hashalg``
      The HMAC digest algorithm to use for signing. The algorithm must be
      supported by the :mod:`hashlib` library. Default: ``'sha512'``.

    ``salt``
      A namespace to avoid collisions between different uses of a shared
      secret. Reusing a secret for different parts of an application is
      strongly discouraged (see :ref:`admonishment_against_secret_sharing`).
      Default: ``'pyramid.session.'``.

    ``cookie_name``
      The name of the cookie used for sessioning. Default: ``'session'``.

    ``max_age``
      The maximum age of the cookie used for sessioning (in seconds).
      Default: ``None`` (browser scope).

    ``path``
      The path used for the session cookie. Default: ``'/'``.

    ``domain``
      The domain used for the session cookie.  Default: ``None`` (no domain).

    ``secure``
      The 'secure' flag of the session cookie. Default: ``False``.

    ``httponly``
      Hide the cookie from Javascript by setting the 'HttpOnly' flag of the
      session cookie. Default: ``False``.

    ``timeout``
      A number of seconds of inactivity before a session times out. If
      ``None`` then the cookie never expires. This lifetime only applies
      to the *value* within the cookie. Meaning that if the cookie expires
      due to a lower ``max_age``, then this setting has no effect.
      Default: ``1200``.

    ``reissue_time``
      The number of seconds that must pass before the cookie is automatically
      reissued as the result of accessing the session. The
      duration is measured as the number of seconds since the last session
      cookie was issued and 'now'.  If this value is ``0``, a new cookie
      will be reissued on every request accessing the session. If ``None``
      then the cookie's lifetime will never be extended.

      A good rule of thumb: if you want auto-expired cookies based on
      inactivity: set the ``timeout`` value to 1200 (20 mins) and set the
      ``reissue_time`` value to perhaps a tenth of the ``timeout`` value
      (120 or 2 mins).  It's nonsensical to set the ``timeout`` value lower
      than the ``reissue_time`` value, as the ticket will never be reissued.
      However, such a configuration is not explicitly prevented.

      Default: ``0``.

    ``set_on_exception``
      If ``True``, set a session cookie even if an exception occurs
      while rendering a view. Default: ``True``.

    ``serializer``
      An object with two methods: ``loads`` and ``dumps``.  The ``loads``
      method should accept bytes and return a Python object.  The ``dumps``
      method should accept a Python object and return bytes.  A ``ValueError``
      should be raised for malformed inputs.  If a serializer is not passed,
      the :class:`pyramid.session.PickleSerializer` serializer will be used.
    """

    if serializer is None:
        serializer = PickleSerializer()

    signed_serializer = SignedSerializer(
            secret + '_internal_use',
            salt + '_internal_use',
            hashalg,
            serializer=serializer,
        )

    serializer = signed_serializer

    @implementer(ISession)
    class PluggableSession(dict):
        """ Dictionary-like session object """

        # configuration parameters
        _cookie_on_exception = set_on_exception
        _timeout = timeout
        _reissue_time = reissue_time

        # dirty flag
        _dirty = False

        def __init__(self, request):
            self._cookie = CookieHelper(
                secret,
                salt,
                cookie_name,
                secure=secure,
                max_age=max_age,
                httponly=httponly,
                path=path,
                domains=domain,
                hashalg=hashalg,
            )
            self._session_id = None
            self.request = request

            reg = request.registry
            plug = reg.queryUtility(IPlugSession)

            if plug is None:
                raise RuntimeError('Unable to find any registered IPlugSession')

            now = time.time()
            created = renewed = now
            new = True
            value = None
            state = {}

            # Get the session_id
            self._session_id = self._cookie.bind(request).get_value()

            if self._session_id is not None:
                try:
                    sess_val = plug.loads(self, request)
                    value = serializer.loads(bytes_(sess_val))
                except ValueError:
                    value = None
                    self._session_id = None

            if value is not None:
                try:
                    rval, cval, sval = value
                    renewed = float(rval)
                    created = float(cval)
                    state = sval
                    new = False
                except (TypeError, ValueError):
                    # value failed to unpack properly or renewed was not
                    # a numeric type so we'll fail deserialization here
                    state = {}

            if self._timeout is not None:
                if now - renewed > self._timeout:
                    # expire the session because it was not renewed
                    # before the timeout threshold
                    state = {}

            if self._session_id is None:
                self._session_id = text_(binascii.hexlify(os.urandom(20)))

            self.created = created
            self.accessed = renewed
            self.renewed = renewed
            self.new = new
            self._plug = plug
            dict.__init__(self, state)

        # ISession methods
        def changed(self):
            if not self._dirty:
                self._dirty = True
                def save_session_callback(request, response):
                    self._save_session(response)
                    self.request = None # explicitly break cycle for gc
                self.request.add_response_callback(save_session_callback)

        def invalidate(self):
            self.clear()

        # non-modifying dictionary methods
        get = manage_accessed(dict.get)
        __getitem__ = manage_accessed(dict.__getitem__)
        items = manage_accessed(dict.items)
        values = manage_accessed(dict.values)
        keys = manage_accessed(dict.keys)
        __contains__ = manage_accessed(dict.__contains__)
        __len__ = manage_accessed(dict.__len__)
        __iter__ = manage_accessed(dict.__iter__)

        if not PY3:
            iteritems = manage_accessed(dict.iteritems)
            itervalues = manage_accessed(dict.itervalues)
            iterkeys = manage_accessed(dict.iterkeys)
            has_key = manage_accessed(dict.has_key)

        # modifying dictionary methods
        clear = manage_changed(dict.clear)
        update = manage_changed(dict.update)
        setdefault = manage_changed(dict.setdefault)
        pop = manage_changed(dict.pop)
        popitem = manage_changed(dict.popitem)
        __setitem__ = manage_changed(dict.__setitem__)
        __delitem__ = manage_changed(dict.__delitem__)

        # flash API methods
        @manage_changed
        def flash(self, msg, queue='', allow_duplicate=True):
            storage = self.setdefault('_f_' + queue, [])
            if allow_duplicate or (msg not in storage):
                storage.append(msg)

        @manage_changed
        def pop_flash(self, queue=''):
            storage = self.pop('_f_' + queue, [])
            return storage

        @manage_accessed
        def peek_flash(self, queue=''):
            storage = self.get('_f_' + queue, [])
            return storage

        # CSRF API methods
        @manage_changed
        def new_csrf_token(self):
            token = text_(binascii.hexlify(os.urandom(20)))
            self['_csrft_'] = token
            return token

        @manage_accessed
        def get_csrf_token(self):
            token = self.get('_csrft_', None)
            if token is None:
                token = self.new_csrf_token()
            return token

        # non-API methods
        def _save_session(self, response):
            if not self._cookie_on_exception:
                exception = getattr(self.request, 'exception', None)
                if exception is not None: # dont set a cookie during exceptions
                    return False

            sess_val = native_(
                    serializer.dumps(
                            (self.accessed, self.created, dict(self))
                        )
                    )

            self._plug.dumps(self, self.request, sess_val)
            self._cookie.set_cookies(self.request.response, self._session_id)

            return True

    return PluggableSession


required_settings =  [
        'secret',
        ]

default_settings = [
    ('cookie_name', str, 'session'),
    ('max_age', int, '864000'),
    ('path', str, '/'),
    ('domain', aslist, ''),
    ('secure', asbool, 'false'),
    ('httponly', asbool, 'true'),
    ('set_on_exception', asbool, 'true'),
    ('timeout', int, '1200'),
    ('reissue_time', int, '0'),
    ('hashalg', str, 'sha512'),
    ('salt', str, 'pyramid_pluggable_session.'),
    ('serializer', str, ''),
]

def parse_settings(settings):
    parsed = {}

    def populate(name, convert, default):
        sname = '%s%s' % ('pluggable_session.', name)
        value = convert(settings.get(sname, default))
        parsed[name] = value

    for name, convert, default in default_settings:
        populate(name, convert, default)
    return parsed

def set_session_plug(config, dotted):
    """ Set the pluggable session that should be used...
    """

    dotted = config.maybe_dotted(dotted)
    config.registry.registerUtility(dotted(), IPlugSession)

def includeme(config):
    # We can't continue unless at least this is set...
    for _required in required_settings:
        _required = 'pluggable_session.' + _required
        if not _required in config.registry.settings:
            raise ValueError(_required +' has to be set in config.settings')

    # Get all of the settings into a neat little dictionary
    settings = parse_settings(config.registry.settings)

    if not settings['domain']:
        del settings['domain']

    if not settings['serializer']:
        del settings['serializer']
    else:
        settings['serializer'] = config.maybe_dotted(settings['serializer'])

    _session_factory = PluggableSessionFactory(
                config.registry.settings['pluggable_session.secret'],
                **settings
            )
    config.set_session_factory(_session_factory)
    config.add_directive('set_session_plug', set_session_plug)

    if 'pluggable_session.plug' in config.registry.settings:
        config.set_session_plug(config.registry.settings['pluggable_session.plug'])

