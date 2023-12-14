#!/usr/bin/env python3

"""RestFS errors"""

# Exit codes

NO_ERROR = 0
CMDCLI_ERROR = 1
SCRIPT_ERROR = 2
CONNECTION_ERROR = 3
UNAUTHORIZED = 4


# Custom exceptions
class ServiceError(Exception):
    """Generic service error"""

    def __init__(self, url='unknown', reason='unknown'):
        self._url_ = url
        self._reason_ = reason

    def __str__(self):
        return f'Service error at "{self._url_}": {self._reason_}'


class Unauthorized(Exception):
    """Authorization error"""

    def __init__(self, user='unknown', reason='unknown'):
        self._user_ = user
        self._reason_ = reason

    def __str__(self):
        return f'Authorization error for user "{self._user_}": {self._reason_}'


class AlreadyLogged(Exception):
    """Try to authorize but already logged with other user"""

    def __init__(self, user='unknown'):
        self._user_ = user

    def __str__(self):
        return f'User "{self._user_}" already logged-in. Logout first!'


class UserAlreadyExists(Exception):
    """Raised if request a new user which already exists"""

    def __init__(self, user='unknown'):
        self._user_ = user

    def __str__(self):
        return f'User "{self._user_}" already exists!'


class UserNotExists(Exception):
    """Raised if request delete a user which not exists"""

    def __init__(self, user='unknown'):
        self._user_ = user

    def __str__(self):
        return f'User "{self._user_}" not exists!'
