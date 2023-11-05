"""Library to access the blob service"""

import json
import hashlib
import os
from pathlib import Path

import requests
from typing import Optional, Union, List

from cli import USER_TOKEN, DEFAULT_ENCODING, HASH_PASS, USER, TOKEN, DOWNLOAD_FOLDER
from cli.blob import Blob
from cli.errors import Unauthorized, BlobServiceError, UserNotExists, AlreadyLogged

CONTENT_JSON = {'Content-Type': 'application/json'}


class BlobService:
    """BlobService implementation"""

    def __init__(self, serviceURL: str, authToken: Optional[str] = None):
        self._url_ = serviceURL[:-1] if serviceURL.endswith('/') else serviceURL
        self._authToken_ = authToken
        self._headers_ = {'AuthToken': authToken} if authToken else {}
        self._blobs_ = []
        if not self.service_up:
            raise BlobServiceError(serviceURL, 'service seems down')

    def createBlob(self, localFilename: Union[str, Path]) -> Blob:
        with open(localFilename, 'rb') as file:
            response = requests.post(f"{self._url_}/api/v1/blob", headers=self._headers_, files={'file': file})
        if response.status_code == 201:
            blob_data = response.json()
            return Blob(blobId=blob_data['blobId'], authToken=self._authToken_)
        else:
            raise BlobServiceError(f"{self._url_}/api/v1/blob", response.content)

    def getBlob(self, blobId: str) -> Blob:
        response = requests.get(f"{self._url_}/api/v1/blob/{blobId}", headers=self._headers_)
        if response.status_code == 200:
            content_dispo = response.headers.get('Content-Disposition', '')
            filename = None
            if 'attachment; filename=' in content_dispo:
                filename = content_dispo.split('filename=')[-1].strip('"')
            if not filename:
                filename = f"blob_{blobId}"
            file_path = os.path.join(DOWNLOAD_FOLDER, filename)
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            return Blob(blobId=blobId, authToken=self._authToken_)
        else:
            raise BlobServiceError(f"{self._url_}/api/v1/blob/{blobId}", response.content)

    def deleteBlob(self, blobId: str) -> None:
        response = requests.delete(f"{self._url_}/api/v1/blob/{blobId}", headers=self._headers_)
        if response.status_code != 204:
            raise BlobServiceError(f"{self._url_}/api/v1/blob/{blobId}", response.content)

    def getBlobs(self) -> List[str]:
        response = requests.get(f"{self._url_}/api/v1/blobs", headers=self._headers_)
        if response.status_code == 200:
            return response.json()
        else:
            raise BlobServiceError(f"{self._url_}/api/v1/blobs", response.content)

    @property
    def service_up(self) -> bool:
        """Check if service is running or not"""
        try:
            result = requests.get(f'{self._url_}/api/v1/status', verify=False)
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

    @property
    def user(self) -> str:
        """Return user"""
        return self._user_

    @property
    def logged(self) -> bool:
        """Return if instance is logged or not"""
        return self._token_ is not None

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

    def token_owner(self, token: str) -> str:
        """Check the owner of a token"""
        result = requests.get(f'{self._url_}/v1/token/{token}', verify=False)
        if result.status_code != 200:
            raise UserNotExists(token=token)
        result = json.loads(result.content.decode(DEFAULT_ENCODING))
        return result[USER]
