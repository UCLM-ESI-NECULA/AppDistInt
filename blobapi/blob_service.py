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

from flask import send_file
from werkzeug.utils import secure_filename

from blobapi import DEFAULT_ENCODING, DEFAULT_STORAGE
from blobapi.errors import ObjectAlreadyExists, ObjectNotFound, Unauthorized

_WRN = logging.warning


def _initialize_(db_file):
    """Create an empty JSON file"""
    _WRN(f'Initializing new database in file "{db_file}"')
    with open(db_file, 'w', encoding=DEFAULT_ENCODING) as contents:
        json.dump({}, contents)


class BlobDB:
    """
        Repository for the blobs
    """

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

        """Add new blob to DB"""
        if url in [blob["URL"] for blob in self._blobs_.values()]:
            raise ObjectAlreadyExists(f'Blob "{url}" already exists')
        if blob_id in self._blobs_:
            raise ObjectAlreadyExists(f'Blob with id:  "{blob_id}" already exists')

        # Save the file
        file.save(url)

        # Save blob info to the database
        self._blobs_[blob_id] = {"URL": url, "public": False, "users": [user]}
        self._commit_()

        return blob_id, url

    def getBlob(self, blob_id, user=None):
        """Retrieve blob by ID"""
        blob_data = self._exists_(blob_id)
        if blob_data["public"] or (user in blob_data["users"]):
            return send_file(blob_data["URL"], as_attachment=True)
        else:
            raise Unauthorized(user=user, reason="User has no permissions to access this blob")

    def removeBlob(self, blob_id, user):
        """Remove blob from DB and filesystem using its ID"""
        blob_data = self._exists_(blob_id)
        if user not in blob_data["users"]:
            raise Unauthorized(user=user, reason="User has no permissions to remove this blob")

        os.remove(blob_data["URL"])
        del self._blobs_[blob_id]
        self._commit_()

    def updateBlob(self, blob_id, new_file):
        """Update blob with a new file"""
        self._exists_(blob_id)

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
        self._blobs_[blob_id] = {"URL": url}
        self._commit_()

    def getBlobHash(self, blob_id):
        """Compute hashes for the blob based on multiple hash types."""

        # Check if blob exists
        blob_data = self._exists_(blob_id)
        blob_path = blob_data["URL"]

        hash_types = ['md5', 'sha1', 'sha256', 'sha512']

        hashes = []

        with open(blob_path, 'rb') as f:
            file_data = f.read()
            for hash_type in hash_types:
                hash_func = getattr(hashlib, hash_type)
                blob_hash = hash_func(file_data).hexdigest()
                hashes.append({"hash_type": hash_type,"hexdigest": blob_hash})

        return hashes

    def setVisibility(self, blob_id, public):
        """Change the visibility of a blob."""
        self._exists_(blob_id)
        self._blobs_[blob_id]['public'] = public
        self._commit_()

    def addPermission(self, blob_id, user):
        """Add read permissions to a user for a blob."""
        self._exists_(blob_id)
        if 'users' not in self._blobs_[blob_id]:
            self._blobs_[blob_id]['users'] = []
        if user not in self._blobs_[blob_id]['users']:
            self._blobs_[blob_id]['users'].append(user)
        self._commit_()

    def removePermission(self, blob_id, user):
        """Remove read permissions from a user for a blob."""
        self._exists_(blob_id)
        if 'users' in self._blobs_[blob_id] and user in self._blobs_[blob_id]['users']:
            self._blobs_[blob_id]['users'].remove(user)
        self._commit_()
