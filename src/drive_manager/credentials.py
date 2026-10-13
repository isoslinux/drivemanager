"""Validated Nextcloud and Proton parameters over encrypted private RC staging."""
from urllib.parse import urlsplit
from .internxt import authorize as encrypted_authorize
from .process import OperationError


def webdav_url(value):
    """Require HTTPS without embedded credentials, query, fragment or whitespace."""
    try:
        if not value or any(char.isspace() or ord(char) < 32 for char in value): raise ValueError()
        parsed = urlsplit(value)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None
            or parsed.password is not None or parsed.query or parsed.fragment): raise ValueError()
        _ = parsed.port
    except ValueError:
        raise OperationError('webdav_url_error') from None
    return value


def authorize(accounts, remote, provider, user, password, cancel, *, url='', code='', mailbox_password='', existing=None):
    if provider not in {'webdav', 'protondrive'} or not user.strip() or not password:
        raise OperationError('credentials_error')
    if cancel.is_set(): raise OperationError('credentials_error')
    if provider == 'webdav':
        parameters = {'url': webdav_url(url.strip()), 'vendor': 'nextcloud',
                      'user': user.strip(), 'pass': password}
    else:
        parameters = {'username': user.strip(), 'password': password, 'enable_caching': 'false'}
        if code.strip(): parameters['2fa'] = code.strip()
        if mailbox_password: parameters['mailbox_password'] = mailbox_password
    return encrypted_authorize(accounts, remote, user, password, cancel, lambda event: '',
                               provider=provider, parameters=parameters, existing=existing)
