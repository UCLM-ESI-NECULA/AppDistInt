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