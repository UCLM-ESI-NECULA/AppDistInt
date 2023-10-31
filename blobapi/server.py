"""API blobapi"""

import argparse
import logging
import sys

from adiauthcli import Client
from adiauthcli.errors import UserNotExists
from flask import Flask, make_response, request
from flask_restx import Api, Resource, fields, reqparse
from werkzeug.datastructures.file_storage import FileStorage
from werkzeug.exceptions import Conflict

from blobapi import DEFAULT_STORAGE, DEFAULT_BLOB_DB, DEFAULT_ADDRESS, DEFAULT_PORT, HTTPS_DEBUG_MODE, ADMIN_TOKEN
from blobapi.blob_service import BlobDB
from blobapi.errors import ObjectAlreadyExists, ObjectNotFound, Unauthorized


def routeApp(app, client: Client, BLOBDB):
    """Route API REST to web"""

    authorizations = {"AuthToken": {"type": "apiKey", "in": "header", "name": "AuthToken"}}
    api = Api(app,
              version='1.0.1',
              title='Object Storage Service',
              description='API for managing blobs or byte packages.',
              authorizations=authorizations,
              security='AuthToken'
              )

    # Namespaces
    status_blob = api.namespace('api/v1/status', description='Status of the service')
    ns_blob = api.namespace('api/v1/blob', description='Blob operations')

    file_upload_parser = reqparse.RequestParser()
    file_upload_parser.add_argument('file',
                                    type=FileStorage,
                                    location='files',
                                    required=True,
                                    help='Upload the blob file')

    # Models for serialization
    blob_model = api.model('Blob', {
        'blobId': fields.String(required=True, description='Blob ID'),
        'URL': fields.String(required=True, description='Blob URL')
    })

    # Define the model for the response
    hash_model = api.model('HashList', {
        'hashes': fields.List(fields.Nested(api.model('Hash', {
            'hash_type': fields.String(required=True, description='Hash Type (e.g., md5, sha256)'),
            'hexdigest': fields.String(required=True, description='The computed hash for the blob')
        })))
    })

    visibility_model = api.model('Visibility', {
        'public': fields.Boolean(required=True, description='Is Blob Public')
    })

    acl_model = api.model('ACL', {
        'user': fields.String(required=True, description='User ID'),
        'allowed_users': fields.List(fields.String, description='Allowed Users')
    })

    def get_client_token():
        auth_token = request.headers.get('AuthToken')
        if not auth_token:
            return make_response('Invalid or missing AuthToken', 401)
        try:
            return client.token_owner(auth_token)
        except UserNotExists:
            return make_response('Invalid or missing AuthToken', 401)

    # Status endpoints
    @status_blob.route('/')
    class StatusCollection(Resource):
        @api.doc('get status of the service')
        def get(self):
            return make_response('Service running', 200)

    # Blob endpoints
    @ns_blob.route('/')
    class BlobCollection(Resource):
        @api.doc('create_blob')
        @api.expect(file_upload_parser)
        @api.marshal_with(blob_model, code=201)
        @api.response(409, 'Conflict')
        @api.response(401, 'Unauthorized')
        @api.header('AuthToken', 'The authorization token', required=True)
        @api.doc(security='AuthToken')
        def post(self):

            # Check if the post request has the file part
            if 'file' not in request.files:
                return make_response('No file', 400)

            file = request.files['file']
            # Check if the user did not select a file
            if file.filename == '':
                return make_response('No selected file', 400)
            try:
                blob_id, url = BLOBDB.newBlob(file, get_client_token())
            except ObjectAlreadyExists as e:
                raise Conflict(description=str(e))

            return {'blobId': blob_id, 'URL': url}, 201

    @ns_blob.route('/<string:blobId>')
    @api.doc(params={'blobId': 'A Blob ID'})
    @api.header('AuthToken', 'The authorization token', required=False)
    @api.doc(security='AuthToken')
    class BlobItem(Resource):
        @api.doc('get_blob')
        @api.response(404, 'Not Found')
        def get(self, blobId):
            auth_token = request.headers.get('AuthToken')
            try:
                if not auth_token:
                    return BLOBDB.getBlob(blobId)
                else:
                    return BLOBDB.getBlob(blobId, get_client_token())
            except ObjectNotFound as e:
                return make_response(e, 404)

        @api.doc('delete_blob')
        @api.response(204, 'Deleted')
        @api.response(404, 'Not Found')
        @api.header('AuthToken', 'The authorization token', required=True)
        @api.doc(security='AuthToken')
        def delete(self, blobId):
            try:
                BLOBDB.removeBlob(blobId, get_client_token())
                return '', 204
            except ObjectNotFound as e:
                return make_response(e, 404)
            except Unauthorized as e:
                return make_response(e, 401)

        @api.doc('update_blob')
        @api.response(204, 'Updated')
        @api.response(404, 'Not Found')
        @api.marshal_with(blob_model, code=204)
        @api.response(409, 'Conflict')
        @api.response(401, 'Unauthorized')
        @api.header('AuthToken', 'The authorization token', required=True)
        @api.doc(security='AuthToken')
        def put(self, blobId):
            # Check if the post request has the file part
            if 'file' not in request.files:
                return make_response('No file', 400)

            file = request.files['file']
            # Check if the user did not select a file
            if file.filename == '':
                return make_response('No selected file', 400)
            try:
                BLOBDB.updateBlob(blobId, file, get_client_token())
            except ObjectAlreadyExists as e:
                raise make_response(e, 409)
            except Unauthorized as e:
                return make_response(e, 401)
            except ObjectNotFound as e:
                return make_response(e, 404)
            return '', 204

    @ns_blob.route('/<string:blobId>/hash')
    @api.doc(params={'blobId': 'A Blob ID'})
    @api.header('AuthToken', 'The authorization token', required=False)
    @api.doc(security='AuthToken')
    class BlobHash(Resource):
        @api.doc('get_blob_hash')
        @api.marshal_with(hash_model)
        def get(self, blobId):
            """Get blob hash"""
            auth_token = request.headers.get('AuthToken')
            try:
                if not auth_token:
                    return {'hashes': BLOBDB.getBlobHash(blobId)}
                else:
                    return {'hashes': BLOBDB.getBlobHash(blobId, get_client_token())}
            except ObjectNotFound as e:
                return make_response(e, 404)

    @ns_blob.route('/<string:blobId>/visibility')
    @api.doc(params={'blobId': 'A Blob ID'})
    class BlobVisibility(Resource):
        @api.doc('set_blob_visibility')
        @api.expect(visibility_model)
        def put(self, blobId):
            return "", 204

    @ns_blob.route('/<string:blobId>/acl')
    @api.doc(params={'blobId': 'A Blob ID'})
    class BlobACL(Resource):
        @api.doc('add_acl')
        @api.expect(acl_model)
        def post(self, blobId):
            return "", 204

        @api.doc('update_acl')
        @api.expect(acl_model)
        def put(self, blobId):
            return "", 204

        @api.doc('get_acl')
        @api.marshal_with(acl_model)
        def get(self, blobId):
            return {'user': 'user1', 'allowed_users': ['user2', 'user3']}

    @ns_blob.route('/<string:blobId>/visibility')
    @api.doc(params={'blobId': 'A Blob ID'})
    class BlobVisibility(Resource):
        parser = reqparse.RequestParser()
        parser.add_argument('public', type=bool, required=True, help='Set visibility to public or private')

        @api.doc('set_blob_visibility')
        @api.response(204, 'Visibility Updated')
        @api.response(401, 'Unauthorized')
        @api.response(404, 'Blob Not Found')
        @api.response(400, 'Bad Request')
        @api.expect(visibility_model, validate=True)
        def put(self, blobId):
            """Set the visibility of a blob."""
            args = self.parser.parse_args()
            try:
                BLOBDB.setVisibility(blobId, args['public'])
                return '', 204
            except ObjectNotFound as e:
                return make_response(e, 404)
            except Exception as e:
                return make_response(e, 400)

        def patch(self, blobId):
            """Alternative to set the visibility of a blob."""
            return self.put(blobId)


#    @ns_blob.route('/<string:blobId>/acl/<string:username>')
#    class BlobUserACL(Resource):
#
#        # For DELETE
#        @api.doc('remove_user_acl')
#        @api.response(204, 'User removed from ACL')
#        @api.response(401, 'Unauthorized')
#        @api.response(404, 'Blob Not Found or User Not in ACL')
#        def delete(self, blobId, username):
#            auth_token = request.headers.get('AuthToken')
#            if not auth_token or not client.ownerOf(auth_token):
#                return make_response('Invalid or missing AuthToken', 401)

#            # Logic to remove 'username' from the allowed_users of blobId in your database
#            # success = BLOBDB.removeUserFromACL(blobId, username)

#            if not success:
#                return make_response(f'User {username} not found in ACL of Blob {blobId}', 404)

#            return '', 204

#    @ns_blob.route('/<string:blobId>/acl')
#    class BlobACL(Resource):
#
#        @api.doc('update_acl')
#        @api.expect(acl_model)
#        @api.response(204, 'ACL Updated')
#        @api.response(401, 'Unauthorized')
#        @api.response(404, 'Blob Not Found')
#        def put(self, blobId):
#            auth_token = request.headers.get('AuthToken')
#            if not auth_token or not client.(auth_token):
#                return make_response('Invalid or missing AuthToken', 401)

#            data = request.json
#            allowed_users = data.get('allowed_users', [])

#            # Logic to update the allowed_users for blobId in your database
#            # BLOBDB.updateACL(blobId, allowed_users)
#
#            return '', 204
#
#        patch = put
#
#        # For GET
#        @api.doc('get_acl')
#        @api.marshal_with(acl_model)
#        def get(self, blobId):
#            auth_token = request.headers.get('AuthToken')
#            if not auth_token or not client.auth_token(auth_token):
#                return make_response('Invalid or missing AuthToken', 401)
#
#            # Logic to retrieve the allowed_users for blobId from your database
#            # allowed_users = BLOBDB.getACL(blobId)
#
#            return {'user': token_manager.ownerOf(auth_token), 'allowed_users': allowed_users}


class ApiService:
    """Wrap all components used by the service"""

    def __init__(self, db_file, client, host=DEFAULT_ADDRESS, port=DEFAULT_PORT):
        self._blobdb_ = BlobDB(db_file)
        self._client_ = client
        self._host_ = host
        self._port_ = port

        self._app_ = Flask(__name__.split('.', maxsplit=1)[0])
        self._app_.config['ERROR_404_HELP'] = False
        routeApp(self._app_, self._client_, self._blobdb_)

    @property
    def base_uri(self):
        """Get the base URI to access the API"""
        host = '127.0.0.1' if self._host_ in ['0.0.0.0'] else self._host_
        return f'http://{host}:{self._port_}'

    def start(self):
        """Start HTTP blobapi"""
        self._app_.run(host=self._host_, port=self._port_, debug=HTTPS_DEBUG_MODE)


def parse_commandline():
    """Parse command line"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-p', '--port', type=int, default=DEFAULT_PORT,
        help='Listening port (default: %(default)s)', dest='port'
    )
    parser.add_argument(
        '-l', '--listening', type=str, default=DEFAULT_ADDRESS,
        help='Listening address (default: all interfaces)', dest='address'
    )
    parser.add_argument(
        '-d', '--db', type=str, default=DEFAULT_BLOB_DB,  # fixme
        help='Database to use (default: %(default)s', dest='db_file'
    )
    parser.add_argument(
        '-s', '--storage', type=str, default=DEFAULT_STORAGE,  # fixme
        help='Database to use (default: %(default)s', dest='storage'
    )
    args = parser.parse_args()
    return args


def main():
    """Entry point for the API"""
    user_options = parse_commandline()

    client = Client("http://localhost:3001", check_service=True)
    service = ApiService(user_options.db_file, client, user_options.address, user_options.port)
    client.login("valentin", "123")
    print(client._get_token_("valentin", "123"))
    try:
        print(f'Starting service on: {service.base_uri}')
        service.start()
    except Exception as error:
        logging.error('Cannot start API: %s', error)
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
