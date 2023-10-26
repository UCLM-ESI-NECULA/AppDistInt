#!/usr/bin/env python3

'''
    Implementacion del servicio de autenticacion
'''

import json
import logging
from pathlib import Path

from blobapi import DEFAULT_ENCODING
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

    def newBlob(self, url):
        """Add new blob to DB"""
        if (url in self._blobs_):
            raise ObjectAlreadyExists(f'Blob "{url}"')
        self._blobs_[url] = url
        self._commit_()

    def removeBlob(self, url):
        """Remove blob from DB"""
        if url not in self._blobs_:
            raise ObjectNotFound(f'Blob "{url}"')
        del self._blobs_[url]
        self._commit_()
