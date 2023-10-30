#!/usr/bin/env python3

'''
    Implementacion del servicio de autenticacion
'''

import json
import logging
import os
import uuid
from pathlib import Path

from flask import jsonify
from werkzeug.utils import secure_filename

from blobapi import DEFAULT_ENCODING, DEFAULT_STORAGE
from blobapi.errors import ObjectAlreadyExists, ObjectNotFound

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

    def newBlob(self, file):
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
        self._blobs_[blob_id] = {"URL": url}
        self._commit_()

        return blob_id, url

    def getBlob(self, blob_id):
        """Retrieve blob data by its ID"""
        if blob_id not in self._blobs_:
            raise ObjectNotFound(f'Blob ID "{blob_id}" not found')
        return self._blobs_[blob_id]

    def removeBlob(self, blob_id):
        """Remove blob from DB using its ID"""
        if blob_id not in self._blobs_:
            raise ObjectNotFound(f'Blob with id: "{blob_id}" not found')
        del self._blobs_[blob_id]
        self._commit_()