#!/usr/bin/env python3
#

'''
    Library to access to ADI AUTH service
'''

import copy
import json
import hashlib
from pathlib import Path

import requests
from typing import Optional, Union, List

from cli import USER_TOKEN, DEFAULT_ENCODING, HASH_PASS, USER, TOKEN
from cli.errors import Unauthorized, BlobServiceError, UserNotExists, AlreadyLogged

CONTENT_JSON = {'Content-Type': 'application/json'}


class Blob:
    allowedUsers = []
    isPrivate = False
    md5 = ''
    sha256 = ''

    def __init__(self, blobId: str, authToken: Optional[str] = None):
        self.blobId = blobId
        self.authToken = authToken
        self.headers = {'AuthToken': authToken} if authToken else {}

    def allowUser(self, username: str) -> None:
        pass

    def delete(self) -> None:
        response = requests.delete(f"{self._url_}/{self.blobId}", headers=self.headers)
        if response.status_code != 200:
            raise BlobServiceError("Error deleting the blob.")

    def dumpToFile(self, localFilename: Union[str, Path, None]) -> None:
        response = requests.get(f"{self._url_}/{self.blobId}", headers=self.headers)
        if response.status_code == 200:
            with open(localFilename, 'wb') as file:
                file.write(response.content)
        else:
            raise BlobServiceError("Error downloading the blob.")

    def revokeUser(self, username: str) -> None:
        pass

    def uploadFromFile(self, localFilename: Union[str, Path]) -> None:
        with open(localFilename, 'rb') as file:
            response = requests.put(f"{self._url_}/{self.blobId}", headers=self.headers, files={'file': file})
        if response.status_code != 200:
            raise BlobServiceError("Error uploading file to blob.")


class BlobService:
    def __init__(self, serviceURL: str, authToken: Optional[str] = None):
        self._url_ = serviceURL[:-1] if serviceURL.endswith('/') else serviceURL
        self._authToken_ = authToken
        self._headers_ = {'AuthToken': authToken} if authToken else {}

        if not self.service_up:
            raise BlobServiceError(serviceURL, 'service seems down')

    def createBlob(self, localFilename: Union[str, Path]) -> Blob:
        with open(localFilename, 'rb') as file:
            response = requests.post(f"{self._url_}/create", headers=self._headers_, files={'file': file})
        if response.status_code == 200:
            blob_data = response.json()
            return Blob(blobId=blob_data['blobId'], authToken=self._authToken_)
        else:
            raise BlobServiceError("Error creating a new blob.")

    def deleteBlob(self, blobId: str) -> None:
        response = requests.delete(f"{self._url_}/{blobId}", headers=self._headers_)
        if response.status_code != 200:
            raise BlobServiceError("Error deleting the blob.")

    def getBlobs(self) -> List[str]:
        pass  # TODO How?

    @property
    def service_up(self) -> bool:
        """Check if service is running or not"""
        try:
            result = requests.get(f'{self._url_}/v1/status', verify=False)
            return result.status_code == 200
        except Exception:
            return False


class AuthService:
    """AuthService implementation"""

    def __init__(self, auth_url: str, authToken: Optional[str] = None):
        self._url_ = auth_url[:-1] if auth_url.endswith('/') else auth_url
        if not self.service_up:
            raise BlobServiceError(auth_url, 'service seems down')

        self._user_ = None
        self._password_ = None
        self._token_ = authToken

    def login(self, user: str, password: str) -> None:
        """Try to login"""
        if self.logged:
            if user != self._user_:
                raise AlreadyLogged(user=self._user_)

        # Refresh auth token
        self._token_ = self._get_token_(user, password)

        self._user_ = user
        self._password_ = password

    @property
    def user(self) -> str:
        """Return user"""
        return self._user_

    @property
    def logged(self) -> bool:
        '''Return if instance is logged or not'''
        return self._token_ is not None

    @property
    def _user_header_(self) -> dict:
        '''Return the user header if available'''
        if not self.logged:
            return {}
        return {USER_TOKEN: self._token_}

    @property
    def service_up(self) -> bool:
        '''Return is service is running or not'''
        try:
            result = requests.get(f'{self._url_}/v1/status', verify=False)
            return result.status_code == 200
        except Exception as error:
            return False

    def login(self, user: str, password: str) -> None:
        '''Try to login'''
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

    def token_owner(self, token: str) -> str:
        """Check the owner of a token"""
        result = requests.get(f'{self._url_}/v1/token/{token}', verify=False)
        if result.status_code != 200:
            raise UserNotExists(token=token)
        result = json.loads(result.content.decode(DEFAULT_ENCODING))
        return result[USER]
