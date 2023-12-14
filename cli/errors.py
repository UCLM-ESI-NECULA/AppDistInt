"""RestFS errors"""

# Exit codes

NO_ERROR = 0
CMDCLI_ERROR = 1
SCRIPT_ERROR = 2
CONNECTION_ERROR = 3
UNAUTHORIZED = 4


# Custom exceptions


class BlobServiceError(Exception):
    """Blob service error"""

    def __init__(self, url='unknown', reason='unknown'):
        self._url_ = url
        self._reason_ = reason

    def __str__(self):
        return f'Blob service error at "{self._url_}": {self._reason_}'


class Unauthorized(Exception):
    """Authorization error"""

    def __init__(self, user='unknown', reason='unknown'):
        self._user_ = user
        self._reason_ = reason

    def __str__(self):
        return f'Authorization error for user "{self._user_}": {self._reason_}'


class InvalidBlob(Exception):

    def __init__(self, url='unknown', reason='unknown'):
        self._url_ = url
        self._reason_ = reason

    def __str__(self):
        return f'Service error at "{self._url_}": {self._reason_}'


class UserNotExists(Exception):
    """Raised if request delete a user which not exists"""

    def __init__(self, token='unknown'):
        self._token_ = token

    def __str__(self):
        return f'User with Token "{self._token_}" not Found'


class AlreadyLogged(Exception):
    """Try to authorize but already logged with other user"""

    def __init__(self, user='unknown'):
        self._user_ = user

    def __str__(self):
        return f'User "{self._user_}" already logged-in. Logout first!'
