#!/usr/bin/env python3

'''
    ADI Auth: Authentication service access library
'''
from cli.authservice import BlobService, AuthService

DEFAULT_ENCODING = 'utf-8'
DEFAULT_PORT = 3001
USER_TOKEN = 'user-token'
HASH_PASS = 'hash-pass'
USER = 'user'
TOKEN = 'token'

def connect(blobUrl: str, authUrl: str, authToken: str) -> BlobService:
    """Factory"""
    client = AuthService(authUrl)
    if authToken:
        service = BlobService(blobUrl, authToken=authToken)
    else:
        service = BlobService(blobUrl)
    return service
