0.0.0a2
=======

- Add better protection against session fixation:
    - Upon failure to deserialize/unpack/expiration of session a new session id
      is generated.
    - Upon calling invalidate() a new session is generated with a new session
      id

- Add more clean-up using the new clear() functionality. When a session fails
  to deserialize, we remove it from the backends, if a session fails to unpack
  we remove it from the backends, and if it has expired we also remove it from
  the backends.

- Update the included backends memory/file/chain to add the new clear()
  function required by IPlugSession.

- Add clear() to IPlugSession interface to allow the session to explicitly have
  the backend plugs remove the session data associated with a certain session
  id.

- On _save_session we set the cookie to response that is provided to us by the
  callback, and not request.response which may not be the users response.

0.0.0a1
=======

New features:

- A file based session storage now exists.

- A chain can now be constructed for session storage

0.0.0dev
========

- A new ISession compliant Pyramid session provider appears.

- A single backend exists, it is based on local Pyramid memory.
