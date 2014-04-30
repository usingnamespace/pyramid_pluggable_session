import logging
log = logging.getLogger(__name__)

import os
import os.path
import tempfile

from zope.interface import implementer

from .interfaces import IPlugSession

@implementer(IPlugSession)
class _FileSessionPlug(object):
    """ File based session

    This pluggable object stores sessions in files, at a config time decided
    location.

    os.rename() is atomic, which means that there is never going to be a case
    that one process is writing while another is reading the same file.
    """

    def loads(self, session, request):
        path = request.registry.settings['pluggable_session.file.path']
        fpath = os.path.join(path, session._session_id)

        try:
            with open(fpath, 'rb') as f:
                return f.read()
        except:
            pass

        return None


    def dumps(self, session, request, sess_data):
        path = request.registry.settings['pluggable_session.file.path']
        fpath = os.path.join(path, session._session_id)

        (fileno, fpath_temp) = tempfile.mkstemp(suffix=session._session_id, dir=path)

        try:
            with os.fdopen(fileno, 'wb') as f:
                f.write(sess_data)

            os.rename(fpath_temp, fpath)
        except (IOError, Exception) as e:
            log.warning('Unable to write new session data to disk...')
            log.exception(e)

    def clear(self, session, request):
        path = request.registry.settings['pluggable_session.file.path']
        fpath = os.path.join(path, session._session_id)

        try:
            os.unlink(fpath)
        except:
            pass


required_settings = [
        'pluggable_session.file.path',
        ]

def FileSessionPlug(config):
    for _require in required_settings:
        if _require not in config.registry.settings:
            raise RuntimeError(_require + ' needs to be set.')

    path = config.registry.settings['pluggable_session.file.path']
    path = os.path.abspath(path)

    if not os.path.isdir(path):
        raise RuntimeError('pluggable_session.file.path is not a path to a directory')
    config.registry.settings['pluggable_session.file.path'] = path

    return _FileSessionPlug()

def includeme(config):
    config.registry.registerUtility(FileSessionPlug(config), IPlugSession)

