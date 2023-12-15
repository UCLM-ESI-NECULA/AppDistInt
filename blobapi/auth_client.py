#!/usr/bin/env python3
#

"""
    Library to access to ADI AUTH service
"""

import copy
import json
import hashlib
from typing import Optional

import requests

from . import ADMIN, USER_TOKEN, ADMIN_TOKEN, USER, HASH_PASS, DEFAULT_ENCODING, TOKEN
from .errors import Unauthorized, ServiceError, UserAlreadyExists, UserNotExists, AlreadyLogged

CONTENT_JSON = {'Content-Type': 'application/json'}


class Client:
    """authClient implementation"""
    def __init__(self, api_url: str, admin_token: Optional[str]=None, check_service: bool=True):
        self._url_ = api_url[:-1] if api_url.endswith('/') else api_url
        if check_service:
            if not self.service_up:
                raise ServiceError(api_url, 'service seems down')
        self._admin_token_ = admin_token

        self._user_ = None
        self._password_ = None
        self._token_ = None

        if admin_token:
            self._admin_token_ = admin_token
            if not self.user_exists(ADMIN):
                raise Unauthorized(user=ADMIN, reason='Invalid administrator token')
            self._user_ = ADMIN
            self._token_ = ""


    @property
    def logged(self) -> bool:
        """Return if instance is logged or not"""
        return self._token_ is not None

    @property
    def administrator(self) -> bool:
        """Return if instance is administrator"""
        return self._admin_token_ is not None

    @property
    def _auth_header_(self) -> dict:
        """Return the administrator header if available"""
        if not self.administrator:
            return {}
        return {ADMIN_TOKEN: self._admin_token_}

    @property
    def _user_header_(self) -> dict:
        """Return the user header if available"""
        if not self.logged:
            return {}
        return {USER_TOKEN: self._token_}

    @property
    def service_up(self) -> bool:
        """Return is service is running or not"""
        try:
            result = requests.get(f'{self._url_}/v1/status', verify=False)
            return result.status_code == 200
        except Exception as error:
            return False

    def login(self, user: str, password: str) -> None:
        """Try to login"""
        if self.logged:
            if user != self._user_:
                raise AlreadyLogged(user=self._user_)

        # Refresh auth token
        self._token_ = self._get_token_(user, password)

        self._user_ = user
        self._password_ = password

    def _get_token_(self, user: str, password: str) -> str:
        """Refresh auth token"""
        if not user or not password:
            raise Unauthorized(user=user, reason='Cannot refresh token without login')
        passwordHash = hashlib.sha256(password.encode(DEFAULT_ENCODING)).hexdigest()
        data = json.dumps({USER: user, HASH_PASS: passwordHash})
        result = requests.post(f'{self._url_}/v1/user/login', data=data, headers=CONTENT_JSON, verify=False)
        if result.status_code != 200:
            raise Unauthorized(user=user, reason=result.content.decode(DEFAULT_ENCODING))
        result = json.loads(result.content.decode(DEFAULT_ENCODING))
        return result[TOKEN]

    @property
    def auth_token(self) -> str:
        """Get current token"""
        return self._token_ if self.logged else None

    def logout(self) -> None:
        """Try to logout"""
        if not self.logged:
            # Log warning
            return
        self._token_ = None
        self._user_ = None
        self._password_ = None

    def refresh_token(self):
        """Re-new auth token"""
        if not self.logged:
            raise Unauthorized(self._user_)
        self._token_ = self._get_token_(self._user_, self._password_)

    def new_user(self, user, password):
        """Create new user"""
        if not self.administrator:
            raise Unauthorized(user="<not administrator>", reason="administrator token not provided")
        if self.user_exists(user):
            raise UserAlreadyExists(user)
        passwordHash = hashlib.sha256(password.encode(DEFAULT_ENCODING)).hexdigest()
        data = json.dumps({USER: user, HASH_PASS: passwordHash})
        headers = copy.copy(CONTENT_JSON)
        headers.update(self._auth_header_)
        result = requests.put(f'{self._url_}/v1/user/{user}', data=data, headers=headers, verify=False)
        if result.status_code != 201:
            if result.status_code == 401:
                raise Unauthorized(self._user_, reason=result.content.decode(DEFAULT_ENCODING))
            if result.status_code == 409:
                raise UserAlreadyExists(user)
            raise Exception("Invalid response from server: ", result.content.decode(DEFAULT_ENCODING))

    def set_user_password(self, user, password):
        """Set new user password"""
        passwordHash = hashlib.sha256(password.encode(DEFAULT_ENCODING)).hexdigest()
        data = json.dumps({USER: user, HASH_PASS: passwordHash})
        if self.administrator:
            result = requests.post(f'{self._url_}/v1/user/{user}', data=data, headers=self._auth_header_, verify=False)
        else:
            expected_user = self.token_owner(self._token_)
            if expected_user != user:
                raise Unauthorized(user=self._user_, reason="User cannot change password of other users")
            result = requests.post(f'{self._url_}/v1/user/{user}', data=data, headers=self._user_header_, verify=False)

        if result.status_code != 202:
            if result.status_code == 404:
                raise UserNotExists(user)
            if result.status_code == 400:
                raise Unauthorized(self._user_, reason=result.content.decode(DEFAULT_ENCODING))
            raise Exception("Invalid response from server: ", result.content.decode(DEFAULT_ENCODING))

    def delete_user(self, user):
        """Create new user"""
        if not self.administrator:
            raise Unauthorized(user="<not administrator>", reason="administrator token not provided")
        if not self.user_exists(user):
            raise UserNotExists(user)
        result = requests.delete(f'{self._url_}/v1/user/{user}', headers=self._auth_header_, verify=False)
        if result.status_code != 204:
            if result.status_code == 401:
                raise Unauthorized(self._user_, reason=result.content.decode(DEFAULT_ENCODING))
            if result.status_code == 404:
                raise UserNotExists(user)
            raise Exception("Invalid response from server: ", result.content.decode(DEFAULT_ENCODING))

    def user_exists(self, user: str) -> bool:
        """Check if user exists or not"""
        if user == ADMIN:
            if not self.administrator:
                raise Unauthorized(user="<not administrator>", reason="administrator token not provided")
            header = self._auth_header_
        else:
            header = {}
        result = requests.get(f'{self._url_}/v1/user/{user}', headers=header, verify=False)
        return result.status_code == 204

    def token_owner(self, token: str) -> str:
        """Check the owner of a token"""
        result = requests.get(f'{self._url_}/v1/token/{token}', verify=False)
        if result.status_code != 200:
            raise UserNotExists(f'Owner of token #{token}')
        result = json.loads(result.content.decode(DEFAULT_ENCODING))
        return result[USER]
