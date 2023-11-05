import os
from pathlib import Path

import requests
from typing import Optional, Union

from cli.errors import BlobServiceError

# FIXME: I don't know how to do it, in the document it doesn't have a api url so i don't know what to do
# I don't understand what is the purpose of this class without the api url


class Blob:
    allowedUsers = []
    isPrivate = False
    md5 = ''
    sha256 = ''
    serviceURL = 'localhost:3002'

    def __init__(self, blobId: str, authToken: Optional[str] = None):
        self._url_ = f"{self.serviceURL}/api/v1/blob"
        self.blobId = blobId
        self.authToken = authToken
        self._headers_ = {'AuthToken': authToken} if authToken else {}

    def allowUser(self, username: str) -> None:
        """Allow access to a user to a blob"""
        response = requests.post(f"{self._url_}/{self.blobId}/acl",
                                 headers=self._headers_,
                                 json={'allowed_users': [username]})
        if response.status_code != 204:
            raise BlobServiceError(f"{self._url_}/{self.blobId}/acl", response.content)

    def revokeUser(self, username: str) -> None:
        """Revoke access to a user to a blob"""
        response = requests.delete(f"{self._url_}/{self.blobId}/acl/{username}",
                                   headers=self._headers_)
        if response.status_code != 204:
            raise BlobServiceError(f"{self._url_}/{self.blobId}/acl/{username}", response.content)

    def deleteBlob(self) -> None:
        """Delete a blob from the blob service"""
        response = requests.delete(f"{self._url_}/api/v1/blob/{self.blobId}", headers=self._headers_)
        if response.status_code != 204:
            raise BlobServiceError(f"{self._url_}/api/v1/blob/{self.blobId}", response.content)

    def dumpToFile(self, localFilename: Union[str, Path, None]) -> None:
        """Download a file from the blob service"""
        response = requests.get(f"{self._url_}/api/v1/blob/{self.blobId}", headers=self._headers_)
        if response.status_code == 200:
            file_path = os.path.join(localFilename)
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
        else:
            raise BlobServiceError(f"{self._url_}/api/v1/blob/{self.blobId}", response.content)

    def uploadFromFile(self, localFilename: Union[str, Path]) -> None:
        """Upload a file to the blob service"""
        with open(localFilename, 'rb') as file:
            response = requests.post(f"{self._url_}/api/v1/blob", headers=self._headers_, files={'file': file})
        if response.status_code != 201:
            raise BlobServiceError(f"{self._url_}/api/v1/blob", response.content)
