#!/usr/bin/env python3

'''
    Implementacion del servicio de autenticacion
'''
import hashlib
import json
import logging
import os
import uuid
from pathlib import Path

from werkzeug.utils import secure_filename

from blobapi import DEFAULT_ENCODING, DEFAULT_STORAGE
from blobapi.errors import ObjectAlreadyExists, ObjectNotFound, UnauthorizedBlob, StatusNotValid

_WRN = logging.warning


def _initialize_(db_file):
    """Create an empty JSON file"""
    _WRN(f'Initializing new database in file "{db_file}"')
    with open(db_file, 'w', encoding=DEFAULT_ENCODING) as contents:
        json.dump({}, contents)


def raise_user_no_owner(blob_data, user):
    if user != blob_data["owner"]:
        raise UnauthorizedBlob(user=user, reason=f'{user} is not the owner of this blob')


def raise_optional_token(blob_data, user):
    if not blob_data["public"] and user != blob_data["owner"] and (not user or user not in blob_data["users"]):
        raise UnauthorizedBlob(user=user, reason="User has no permissions for this blob")


class BlobDB:
    """Repository for the blobs"""

    def __init__(self, db_file):
        if not Path(db_file).exists():
            _initialize_(db_file)
        self._db_file_ = db_file
        self._blobs_ = {}
        self._read_db_()

    def _read_db_(self):
        with open(self._db_file_, 'r', encoding=DEFAULT_ENCODING) as contents:
            self._blobs_ = json.load(contents)

    def _commit_(self):
        with open(self._db_file_, 'w', encoding=DEFAULT_ENCODING) as contents:
            json.dump(self._blobs_, contents, indent=2, sort_keys=True)

    def _exists_(self, blob_id):
        if blob_id not in self._blobs_:
            raise ObjectNotFound(blob_id)
        return self._blobs_[blob_id]

    def newBlob(self, file, user):
        # Save the file and generate blob metadata
        if not file:
            raise ValueError("File not provided")
        filename = secure_filename(file.filename)
        url = os.path.join(DEFAULT_STORAGE, filename)
        blob_id = str(uuid.uuid4())

        storage_path = os.path.dirname(url)
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

        """Add new blob to DB"""
        if url in [blob["URL"] for blob in self._blobs_.values()]:
            raise ObjectAlreadyExists(url)
        if blob_id in self._blobs_:
            raise ObjectAlreadyExists(blob_id)

        # Save the file
        file.save(url)

        # Save blob info to the database
        self._blobs_[blob_id] = {"URL": url, "public": False, "users": [], "owner": user}
        self._commit_()

        return blob_id, url

    def getBlob(self, blob_id, user=None):
        """Retrieve blob by ID"""
        blob_data = self._exists_(blob_id)

        raise_optional_token(blob_data, user)
        return blob_data["URL"]

    def removeBlob(self, blob_id, user):
        """Remove blob from DB and filesystem using its ID"""
        blob_data = self._exists_(blob_id)
        raise_user_no_owner(blob_data, user)

        os.remove(blob_data["URL"])
        del self._blobs_[blob_id]
        self._commit_()

    def updateBlob(self, blob_id, new_file, user):
        """Update blob with a new file"""
        self._exists_(blob_id)
        raise_user_no_owner(self._blobs_[blob_id], user)

        filename = secure_filename(new_file.filename)
        url = os.path.join(DEFAULT_STORAGE, filename)

        # Check for potential conflicts
        if url in [blob["URL"] for blob in self._blobs_.values()] and self._blobs_[blob_id]["URL"] != url:
            raise ObjectAlreadyExists(f'Blob "{url}" already exists')

        # Remove the old file
        os.remove(self._blobs_[blob_id]["URL"])

        # Save the new file
        new_file.save(url)

        # Update blob info in the database
        self._blobs_[blob_id]["URL"] = url
        self._commit_()

    def getBlobHash(self, blob_id, user):
        """Compute hashes for the blob based on multiple hash types."""
        blob_data = self._exists_(blob_id)
        raise_optional_token(blob_data, user)
        hash_types = ['md5', 'sha1', 'sha256', 'sha512']
        hashes = []
        with open(blob_data["URL"], 'rb') as f:
            file_data = f.read()
            for hash_type in hash_types:
                hash_func = getattr(hashlib, hash_type)
                blob_hash = hash_func(file_data).hexdigest()
                hashes.append({"hash_type": hash_type, "hexdigest": blob_hash})

        return hashes

    def setVisibility(self, blob_id, public, user):
        """Change the visibility of a blob."""
        self._exists_(blob_id)
        raise_user_no_owner(self._blobs_[blob_id], user)
        if self._blobs_[blob_id]['public'] != public:
            self._blobs_[blob_id]['public'] = public
        else:
            raise StatusNotValid(blob_id, f'Blob is already {"public" if public else "private"}')
        self._commit_()

    def getPermissions(self, blob_id, owner):
        """Get read permissions for a blob."""
        blob_data = self._exists_(blob_id)
        raise_user_no_owner(blob_data, owner)
        users = blob_data['users']
        users.append(blob_data['owner'])
        return users

    def addPermission(self, blob_id, users, owner):
        """Add read permissions for a blob."""
        self._exists_(blob_id)
        raise_user_no_owner(self._blobs_[blob_id], owner)
        for user in users:
            if user not in self._blobs_[blob_id]['users'] and user != self._blobs_[blob_id]['owner']:
                self._blobs_[blob_id]['users'].append(user)
        self._commit_()

    def removePermission(self, blob_id, user, owner):
        """Remove read permissions from a user for a blob."""
        self._exists_(blob_id)
        raise_user_no_owner(self._blobs_[blob_id], owner)
        if 'users' in self._blobs_[blob_id] and user in self._blobs_[blob_id]['users']:
            self._blobs_[blob_id]['users'].remove(user)
        else:
            raise ObjectNotFound(user)
        self._commit_()

    def updatePermission(self, blob_id, users, owner):
        """Update read permissions from a user for a blob."""
        self._exists_(blob_id)
        raise_user_no_owner(self._blobs_[blob_id], owner)
        if users is not None and self._blobs_[blob_id]['owner'] in users:
            users.remove(self._blobs_[blob_id]['owner'])
        self._blobs_[blob_id]['users'] = users
        self._commit_()
