import unittest
import tempfile
import os
from io import BytesIO
from pathlib import Path

from flask import Flask

from blobapi import DEFAULT_STORAGE
from blobapi.blob_service import BlobDB
from werkzeug.datastructures import FileStorage

from blobapi.errors import UnauthorizedBlob, ObjectNotFound
from blobapi.server import routeApp

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

    def tearDown(self):
        """Cleanup the temporary directory and file after tests."""
        os.system('rm -rf ' + DEFAULT_STORAGE)
        self.workspace.cleanup()

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

    def test_getBlobs(self):
        """Test retrieving a list of blobs based on user permissions."""

        # Set up mock blobs in the database
        self.blob_service._blobs_ = {
            'blob_id1': {'public': True, 'owner': 'user1', 'users': [], 'URL': 'blob1'},
            'blob_id2': {'public': False, 'owner': 'user2', 'users': ['user1'], 'URL': 'blob2'},
            'blob_id3': {'public': False, 'owner': 'user3', 'users': [], 'URL': 'blob3'},
        }

        # Define the expected results for user1
        expected_results_user1 = [
            {'blobId': 'blob_id1', 'URL': 'blob1'},
            {'blobId': 'blob_id2', 'URL': 'blob2'},
        ]
        actual_results_user1 = self.blob_service.getBlobs(user='user1')
        self.assertCountEqual(actual_results_user1, expected_results_user1)

        expected_results_user2 = [
            {'blobId': 'blob_id1', 'URL': 'blob1'},
            {'blobId': 'blob_id2', 'URL': 'blob2'},
        ]
        actual_results_user2 = self.blob_service.getBlobs(user='user2')
        self.assertCountEqual(actual_results_user2, expected_results_user2)

        # public blobs
        expected_results_anonymous = [
            {'blobId': 'blob_id1', 'URL': 'blob1'},
        ]
        actual_results_anonymous = self.blob_service.getBlobs()
        self.assertCountEqual(actual_results_anonymous, expected_results_anonymous)

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


class MockClient:
    def token_owner(self, auth_token):
        return 'user_id'

    def login(self, username, password):
        return True


class MockBlobDB:
    def newBlob(self, file, token):
        return 'blob_id', 'blob_url'

    def getBlob(self, blob_id, token):
        return 'test_file'

    def removeBlob(self, blob_id, token):
        pass

    def updateBlob(self, blob_id, file, token):
        pass

    def getBlobHash(self, blob_id, token):
        return [{'hash_type': 'md5', 'hexdigest': 'hash_value'}]

    def setVisibility(self, blob_id, public, token):
        pass

    def addPermission(self, blob_id, allowed_users, token):
        pass

    def updatePermission(self, blob_id, allowed_users, token):
        pass

    def getPermissions(self, blob_id, token):
        return ['user1', 'user2']

    def removePermission(self, blob_id, username, token):
        pass


class TestBlobApi(unittest.TestCase):
    AUTH_TOKEN = 'test-token'

    def get_auth_header(self):
        return {'AuthToken': self.AUTH_TOKEN}

    def setUp(self):
        self.client = MockClient()
        self.blobdb = MockBlobDB()

        app = Flask(__name__)
        routeApp(app, self.client, self.blobdb)
        app.testing = True
        self.app = app.test_client()

    def test_get_status(self):
        response = self.app.get('/api/v1/status/')
        self.assertEqual(response.status_code, 200)

    def test_create_blob(self):
        data = {'file': (BytesIO(b'Content'), 'test.txt')}
        response = self.app.post('/api/v1/blob/', data=data,
                                 content_type='multipart/form-data',
                                 headers=self.get_auth_header())
        self.assertEqual(response.status_code, 201)

    def test_create_blob_without_file(self):
        data = {}
        response = self.app.post('/api/v1/blob/', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)

    def test_get_blob(self):
        response = self.app.get('/api/v1/blob/blob_id')
        self.assertEqual(response.status_code, 200)

    def test_delete_blob(self):
        response = self.app.delete('/api/v1/blob/blob_id', headers=self.get_auth_header())
        self.assertEqual(response.status_code, 204)

    def test_delete_blob_unauthorized(self):
        response = self.app.delete('/api/v1/blob/unauthorized_blob_id')
        self.assertEqual(response.status_code, 401)

    def test_update_blob(self):
        data = {'file': (BytesIO(b'new file contents'), 'test_update.txt')}
        response = self.app.put('/api/v1/blob/blob_id', data=data, content_type='multipart/form-data',
                                headers=self.get_auth_header())
        self.assertEqual(response.status_code, 204)

    def test_update_blob_unauthorized(self):
        data = {'file': (BytesIO(b'new file contents'), 'test_update.txt')}
        response = self.app.put('/api/v1/blob/unauthorized_blob_id', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 401)

    def test_get_blob_hash(self):
        response = self.app.get('/api/v1/blob/blob_id/hash')
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
