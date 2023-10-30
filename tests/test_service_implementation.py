#!/usr/bin/env python3

import os.path
import tempfile
import unittest
from pathlib import Path

from blobapi import DEFAULT_ENCODING
from blobapi.blob_service import BlobDB
from blobapi.errors import ObjectNotFound

ADMIN_TOKEN = 'test_admin_token'
WRONG_TOKEN = 'this_token_should_not_exists'
NOT_EXISTING_BLOB = 'not_existing_blob'
USER1 = 'test_blob1'
USER2 = 'test_blob2'
HASH1 = 'test_blob1_hash'
NEW_HASH1 = 'test_blob1_hash_new'
WRONG_HASH1 = 'test_blob1_hash_but_wrong'


class TestPersistentDB(unittest.TestCase):

    def test_creation(self):
        """Test initialization"""
        with tempfile.TemporaryDirectory() as workspace:
            dbfile = Path(workspace).joinpath('dbfile.json')
            self.assertFalse(os.path.exists(dbfile))
            BlobDB(db_file=dbfile)
            self.assertTrue(os.path.exists(dbfile))
            with open(dbfile, 'r', encoding=DEFAULT_ENCODING) as f:
                content = f.read()
            self.assertEqual(content, "{}")

    def test_remove_not_exists_blob(self):
        """Test remove not-exists blob"""
        with tempfile.TemporaryDirectory() as workspace:
            dbfile = Path(workspace).joinpath('dbfile.json')
            blobdb = BlobDB(db_file=dbfile)

            with self.assertRaises(ObjectNotFound):
                blobdb.removeBlob(NOT_EXISTING_BLOB)
