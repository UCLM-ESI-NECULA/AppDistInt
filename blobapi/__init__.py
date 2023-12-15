"""Configuration file for the rest API"""
import os

from dotenv import load_dotenv
load_dotenv()

BLOB_SERVICE_PORT = os.getenv('BLOB_SERVICE_PORT', '3002')
BLOB_SERVICE_ADDRESS = os.getenv('BLOB_SERVICE_ADDRESS', '0.0.0.0')
AUTH_PORT=os.getenv('AUTH_PORT', '3001')
AUTH_ADDRESS=os.getenv('AUTH_ADDRESS', '127.0.0.1')
DEFAULT_ENCODING = os.getenv('DEFAULT_ENCODING', 'utf-8')
FILE_STORAGE = os.getenv('FILE_STORAGE', 'storage')
BLOB_DB = os.getenv('BLOB_DB', 'blobs.json')

HTTPS_DEBUG_MODE = False
ADMIN = 'admin'

ADMIN_TOKEN = 'admin-token'
USER_TOKEN = 'user-token'
USER = 'user'
TOKEN = 'token'
HASH_PASS = 'hash-pass'
