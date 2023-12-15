"""Rest Api errors"""


# Custom exceptions

class UnauthorizedBlob(Exception):
    """Authorization error"""

    def __init__(self, user='unknown', reason='unknown'):
        self._user_ = user
        self._reason_ = reason

    def __str__(self):
        return f'Authorization error for user "{self._user_}": {self._reason_}'

class StatusNotValid(Exception):
    """Status error"""

    def __init__(self, item='unknown', reason='unknown'):
        self._item_ = item
        self._reason_ = reason
    def __str__(self):
        return f'Status error for blob "{self._item_}": {self._reason_}'


class ObjectNotFound(Exception):
    """Object not found error"""

    def __init__(self, item='unknown'):
        self._item_ = item

    def __str__(self):
        return f'Requested item "{self._item_}" not found'


class ObjectAlreadyExists(Exception):
    """Object already exists error"""

    def __init__(self, item='unknown'):
        self._item_ = item

    def __str__(self):
        return f'Trying to create already created item "{self._item_}"'

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
