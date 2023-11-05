"""API blobapi"""

import argparse
import logging
import sys

from adiauthcli import Client
from adiauthcli.errors import UserNotExists
from flask import Flask, make_response, request, send_file
from flask_restx import Api, Resource, fields, reqparse
from werkzeug.datastructures.file_storage import FileStorage
from werkzeug.exceptions import Conflict, Unauthorized, BadRequest, NotFound

from blobapi import DEFAULT_STORAGE, DEFAULT_BLOB_DB, DEFAULT_ADDRESS, DEFAULT_PORT, HTTPS_DEBUG_MODE
from blobapi.blob_service import BlobDB
from blobapi.errors import ObjectAlreadyExists, ObjectNotFound, UnauthorizedBlob, StatusNotValid


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
    ns_blobs = api.namespace('api/v1/blobs', description='Blobs operations')

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
        'user': fields.String(required=False, description='Allowed user'),
        'allowed_users': fields.List(fields.String, required=True, description='Allowed Users')
    })

    acl_model_update = api.model('ACL', {
        'allowed_users': fields.List(fields.String, required=True, description='Allowed Users')
    })

    blob_model = api.model('Blob', {
        'blobId': fields.String(required=True, description='The blob identifier'),
        'URL': fields.String(required=True, description='The URL of the blob'),
    })

    def get_client_token():
        auth_token = request.headers.get('AuthToken')
        if auth_token:
            try:
                return client.token_owner(auth_token)
            except UserNotExists:
                raise Unauthorized('Invalid AuthToken')
        raise Unauthorized(description="Missing token")

    def get_optional_client_token():
        auth_token = request.headers.get('AuthToken')
        return client.token_owner(auth_token) if auth_token else None

    # Status endpoints
    @status_blob.route('/')
    class StatusCollection(Resource):
        @api.doc('get status of the service')
        def get(self):
            return make_response('Service running', 200)

    @ns_blobs.route('/')
    class BlobsCollection(Resource):
        @api.doc('get_blobs')
        @api.response(401, 'Unauthorized')
        @api.marshal_list_with(blob_model)
        def get(self):
            """Get all blobs"""
            return BLOBDB.getBlobs(user=get_optional_client_token())

    # Blob endpoints
    @ns_blob.route('/')
    class BlobCollection(Resource):
        @api.doc('create_blob')
        @api.expect(file_upload_parser)
        @api.marshal_with(blob_model, code=201)
        @api.response(409, 'Conflict')
        @api.response(401, 'Unauthorized')
        def post(self):

            # Check if the post request has the file part
            if 'file' not in request.files:
                raise BadRequest('No file')

            file = request.files['file']
            if file.filename == '':
                return BadRequest('No selected file')
            try:
                blob_id, url = BLOBDB.newBlob(file, get_client_token())
            except ObjectAlreadyExists as e:
                raise Conflict(description=str(e))
            return {'blobId': blob_id, 'URL': url}, 201

    @ns_blob.route('/<string:blobId>')
    @api.doc(params={'blobId': 'A Blob ID'})
    class BlobItem(Resource):
        @api.doc('get_blob')
        @api.response(404, 'Not Found')
        @api.response(401, 'Unauthorized')
        def get(self, blobId):
            try:
                 file_path = BLOBDB.getBlob(blobId, get_optional_client_token())
                 return send_file(file_path, as_attachment=True)
            except ObjectNotFound as e:
                raise NotFound(description=str(e))
            except UnauthorizedBlob as e:
                raise Unauthorized(description=str(e))

        @api.doc('delete_blob')
        @api.response(204, 'Deleted')
        @api.response(404, 'Not Found')
        @api.response(401, 'Unauthorized')
        def delete(self, blobId):
            try:
                BLOBDB.removeBlob(blobId, get_client_token())
                return '', 204
            except ObjectNotFound as e:
                raise NotFound(description=str(e))
            except UnauthorizedBlob as e:
                raise Unauthorized(description=str(e))

        @api.doc('update_blob')
        @api.response(204, 'Updated')
        @api.response(404, 'Not Found')
        @api.marshal_with(blob_model, code=204)
        @api.response(409, 'Conflict')
        @api.response(401, 'Unauthorized')
        @api.expect(file_upload_parser)
        def put(self, blobId):
            if 'file' not in request.files:
                return BadRequest('No  file')

            file = request.files['file']
            if file.filename == '':
                return BadRequest('No selected file')
            try:
                BLOBDB.updateBlob(blobId, file, get_client_token())
            except ObjectAlreadyExists as e:
                raise Conflict(description=str(e))
            except UnauthorizedBlob as e:
                raise Unauthorized(description=str(e))
            except ObjectNotFound as e:
                raise NotFound(description=str(e))
            return '', 204

    @ns_blob.route('/<string:blobId>/hash')
    @api.doc(params={'blobId': 'A Blob ID'})
    class BlobHash(Resource):
        @api.doc('get_blob_hash')
        @api.response(404, 'Not Found')
        @api.response(401, 'Unauthorized')
        @api.marshal_with(hash_model)
        def get(self, blobId):
            """Get blob hash"""
            try:
                return {'hashes': BLOBDB.getBlobHash(blobId, get_optional_client_token())}
            except ObjectNotFound as e:
                raise NotFound(description=str(e))
            except UnauthorizedBlob as e:
                raise Unauthorized(description=str(e))

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
            if args['public'] is None:
                raise BadRequest(description="Missing public")
            try:
                BLOBDB.setVisibility(blobId, args['public'], get_client_token())
                return '', 204
            except ObjectNotFound as e:
                raise NotFound(description=str(e))
            except StatusNotValid as e:
                raise BadRequest(description=str(e))
            except UnauthorizedBlob as e:
                raise Unauthorized(description=str(e))

        patch = put

    @ns_blob.route('/<string:blobId>/acl')
    @api.doc(params={'blobId': 'A Blob ID'})
    class BlobACL(Resource):

        @api.doc('create_acl')
        @api.expect(acl_model)
        @api.response(204, 'ACL Created')
        @api.response(401, 'Unauthorized')
        @api.response(404, 'Blob Not Found')
        @api.response(400, 'Bad Request')
        def post(self, blobId):
            data = request.json
            allowed_users = data.get('allowed_users')

            if allowed_users is not None:
                if not isinstance(allowed_users, list) or not all(isinstance(item, str) for item in allowed_users):
                    raise BadRequest(description="Allowed users must be a list of strings")

            user = data.get('user', None)
            if allowed_users is None and user is None:
                raise BadRequest(description="Missing allowed_users or user")

            if allowed_users is not None and user is not None:
                raise BadRequest(description="Cannot use both allowed_users and user")

            allowed_users = allowed_users if allowed_users is not None else [user]
            try:
                BLOBDB.addPermission(blobId, allowed_users, get_client_token())
            except ObjectNotFound as e:
                raise NotFound(description=str(e))
            except UnauthorizedBlob as e:
                raise Unauthorized(description=str(e))
            return '', 204

        @api.doc('update_acl')
        @api.expect(acl_model_update)
        @api.response(204, 'ACL Updated')
        @api.response(401, 'Unauthorized')
        @api.response(404, 'Blob Not Found')
        @api.response(400, 'Bad Request')
        def put(self, blobId):
            data = request.json
            allowed_users = data.get('allowed_users', [])
            if allowed_users is None:
                raise BadRequest(description="Missing allowed_users")
            try:
                BLOBDB.updatePermission(blobId, allowed_users, get_client_token())
            except ObjectNotFound as e:
                raise NotFound(description=str(e))
            except UnauthorizedBlob as e:
                raise Unauthorized(description=str(e))
            return '', 204

        patch = put

        # For GET
        @api.doc('get_acl')
        @api.response(404, 'Blob Not Found')
        @api.response(401, 'Unauthorized')
        @api.marshal_with(acl_model_update, 200)
        def get(self, blobId):
            try:
                return {'allowed_users': BLOBDB.getPermissions(blobId, get_client_token())}
            except ObjectNotFound as e:
                raise NotFound(description=str(e))
            except UnauthorizedBlob as e:
                raise Unauthorized(description=str(e))

    @ns_blob.route('/<string:blobId>/acl/<string:username>')
    class BlobUserACL(Resource):

        @api.doc('remove_user_acl')
        @api.response(204, 'User removed from ACL')
        @api.response(401, 'Unauthorized')
        @api.response(404, 'Blob Not Found or User Not in ACL')
        def delete(self, blobId, username):
            try:
                BLOBDB.removePermission(blobId, username, get_client_token())
            except UnauthorizedBlob as e:
                raise Unauthorized(description=str(e))
            except ObjectNotFound as e:
                raise NotFound(description=str(e))
            return '', 204

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
    # client.login("valentin", "123")
    client.login("pablo", "123")
    print(client._get_token_("valentin", "123"))
    print(client._get_token_("pablo", "123"))
    try:
        print(f'Starting service on: {service.base_uri}')
        service.start()
    except Exception as error:
        logging.error('Cannot start API: %s', error)
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
