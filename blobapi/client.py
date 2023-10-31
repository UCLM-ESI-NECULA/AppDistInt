import requests
from typing import Optional, List, Union
from pathlib import Path


# Exception Definitions
class InvalidBlob(Exception):
    pass


class Unauthorized(Exception):
    pass


class BlobServiceError(Exception):
    pass


class Blob:
    accessUrl = 'localhost:3002'
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
        response = requests.delete(f"{self.accessUrl}/{self.blobId}", headers=self.headers)
        if response.status_code != 200:
            raise BlobServiceError("Error deleting the blob.")

    def dumpToFile(self, localFilename: Union[str, Path, None]) -> None:
        response = requests.get(f"{self.accessUrl}/{self.blobId}", headers=self.headers)
        if response.status_code == 200:
            with open(localFilename, 'wb') as file:
                file.write(response.content)
        else:
            raise BlobServiceError("Error downloading the blob.")

    def revokeUser(self, username: str) -> None:
        pass

    def uploadFromFile(self, localFilename: Union[str, Path]) -> None:
        with open(localFilename, 'rb') as file:
            response = requests.put(f"{self.accessUrl}/{self.blobId}", headers=self.headers, files={'file': file})
        if response.status_code != 200:
            raise BlobServiceError("Error uploading file to blob.")


class BlobService:
    def __init__(self, serviceURL: str, authToken: Optional[str] = None):
        self.serviceURL = serviceURL
        self.authToken = authToken
        self.headers = {'AuthToken': authToken} if authToken else {}

    def createBlob(self, localFilename: Union[str, Path]) -> Blob:
        with open(localFilename, 'rb') as file:
            response = requests.post(f"{self.serviceURL}/create", headers=self.headers, files={'file': file})
        if response.status_code == 200:
            blob_data = response.json()
            return Blob(blobId=blob_data['blobId'], authToken=self.authToken)
        else:
            raise BlobServiceError("Error creating a new blob.")

    def deleteBlob(self, blobId: str) -> None:
        response = requests.delete(f"{self.serviceURL}/{blobId}", headers=self.headers)
        if response.status_code != 200:
            raise BlobServiceError("Error deleting the blob.")

    def getBlobs(self) -> List[str]:
        pass  # TODO How?
