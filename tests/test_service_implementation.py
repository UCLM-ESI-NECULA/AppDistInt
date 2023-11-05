import unittest
import tempfile
import os
from pathlib import Path

from blobapi import DEFAULT_ENCODING
from blobapi.blob_service import BlobDB
from werkzeug.datastructures import FileStorage

from blobapi.errors import UnauthorizedBlob, ObjectNotFound

# Constants defined for the purpose of testing
USER1 = 'test_user1'
USER2 = 'test_user2'
HASH1 = 'test_blob1_hash'


class TestPersistentDB(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory and db file for tests."""
        self.workspace = tempfile.TemporaryDirectory()
        self.dbfile = Path(self.workspace.name).joinpath('dbfile.json')
        self.blob_service = BlobDB(db_file=self.dbfile)
        self.assertTrue(os.path.exists(self.dbfile))
        # Setup a test file to use in the tests

        self.test_file = tempfile.NamedTemporaryFile()
        self.test_file_storage = FileStorage(stream=self.test_file,
                                             filename=self.test_file.name,
                                             content_type='text/plain')

    def test_newBlob(self):
        """Test the creation of a new blob."""
        blob_id, url = self.blob_service.newBlob(self.test_file_storage, USER1)
        self.assertIsNotNone(blob_id)
        self.assertIsNotNone(url)
        # Verify blob data
        blob_data = self.blob_service._blobs_[blob_id]
        self.assertEqual(blob_data['owner'], USER1)
        self.assertFalse(blob_data['public'])
        self.assertListEqual(blob_data['users'], [])
        self.assertTrue(os.path.exists(url))

    def test_getBlob(self):
        """Test retrieving a blob."""
        blob_id, _ = self.blob_service.newBlob(self.test_file_storage, USER1)
        # Test with correct permissions
        response = self.blob_service.getBlob(blob_id, USER1)
        self.assertTrue(response)
        # Test with no permissions
        with self.assertRaises(UnauthorizedBlob):
            self.blob_service.getBlob(blob_id, USER2)

    def test_removeBlob(self):
        """Test removing a blob."""
        blob_id, _ = self.blob_service.newBlob(self.test_file_storage, USER1)
        # Try to remove with incorrect user
        with self.assertRaises(UnauthorizedBlob):
            self.blob_service.removeBlob(blob_id, USER2)
        # Remove with correct user
        self.blob_service.removeBlob(blob_id, USER1)
        # Check if file is removed
        with self.assertRaises(ObjectNotFound):
            self.blob_service._exists_(blob_id)

    def test_updateBlob(self):
        """Test updating a blob."""
        blob_id, _ = self.blob_service.newBlob(self.test_file_storage, USER1)
        # Try to update with incorrect user
        with tempfile.NamedTemporaryFile() as update_file:
            update_file_storage = FileStorage(stream=update_file,
                                              filename=update_file.name,
                                              content_type='text/plain')
            with self.assertRaises(UnauthorizedBlob):
                self.blob_service.updateBlob(blob_id, update_file_storage, USER2)
        # Update with correct user
        self.blob_service.updateBlob(blob_id, self.test_file_storage, USER1)

    def test_getBlobHash(self):
        """Test getting blob hash."""
        blob_id, _ = self.blob_service.newBlob(self.test_file_storage, USER1)
        hashes = self.blob_service.getBlobHash(blob_id, USER1)
        # Check if correct hashes are returned
        self.assertIsInstance(hashes, list)
        self.assertTrue(any(hash_dict['hash_type'] == 'md5' for hash_dict in hashes))

    def test_setVisibility(self):
        """Test setting visibility of a blob."""
        blob_id, _ = self.blob_service.newBlob(self.test_file_storage, USER1)
        # Set visibility with correct user
        self.blob_service.setVisibility(blob_id, True, USER1)
        self.assertTrue(self.blob_service._blobs_[blob_id]['public'])
        # Try to set visibility with incorrect user
        with self.assertRaises(UnauthorizedBlob):
            self.blob_service.setVisibility(blob_id, False, USER2)

    def test_getPermissions(self):
        """Test retrieving blob permissions."""
        blob_id, _ = self.blob_service.newBlob(self.test_file_storage, USER1)
        permissions = self.blob_service.getPermissions(blob_id, USER1)
        self.assertIn(USER1, permissions)
        # Test with incorrect user
        with self.assertRaises(UnauthorizedBlob):
            self.blob_service.getPermissions(blob_id, USER2)

    def test_addPermission(self):
        """Test adding permissions to a blob."""
        blob_id, _ = self.blob_service.newBlob(self.test_file_storage, USER1)
        # Add permission with correct user
        self.blob_service.addPermission(blob_id, [USER2], USER1)
        self.assertIn(USER2, self.blob_service._blobs_[blob_id]['users'])

    def test_removePermission(self):
        """Test removing permissions from a blob."""
        blob_id, _ = self.blob_service.newBlob(self.test_file_storage, USER1)
        # Try to remove permissions with incorrect user
        with self.assertRaises(UnauthorizedBlob):
            self.blob_service.removePermission(blob_id, USER2, USER2)
        # Remove permissions with correct user
        self.blob_service.addPermission(blob_id, [USER2], USER1)
        self.blob_service.removePermission(blob_id, USER2, USER1)
        self.assertNotIn(USER2, self.blob_service._blobs_[blob_id]['users'])

    def test_updatePermission(self):
        """Test updating permissions for a blob."""
        blob_id, _ = self.blob_service.newBlob(self.test_file_storage, USER1)
        # Update permissions with correct user
        self.blob_service.updatePermission(blob_id, [USER2], USER1)
        self.assertNotIn(USER1, self.blob_service._blobs_[blob_id]['users'])
        self.assertIn(USER2, self.blob_service._blobs_[blob_id]['users'])
        # Try to update permissions with incorrect user
        with self.assertRaises(UnauthorizedBlob):
            self.blob_service.updatePermission(blob_id, [USER1], USER2)


if __name__ == '__main__':
    unittest.main()
