from pathlib import Path

import requests
from typing import Optional, Union

from cli.errors import BlobServiceError


class Blob:
    allowedUsers = []
    isPrivate = False
    md5 = ''
    sha256 = ''
    serviceURL = ''

    def __init__(self, blobId: str, authToken: Optional[str] = None):
        self.blobId = blobId
        self.authToken = authToken
        self.headers = {'AuthToken': authToken} if authToken else {}

    def allowUser(self, username: str) -> None:
        response = requests.post(f"{self._url_}/{self.blobId}/user/{username}", headers=self.headers)
        if response.status_code != 200:
            raise BlobServiceError("Error allowing user to blob.")

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
