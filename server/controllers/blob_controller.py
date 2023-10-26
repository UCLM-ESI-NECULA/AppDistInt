from flask_restx import Api, Resource, fields, Namespace
from server.models.blob import blob_model

authorizations = {
    "jsonWebToken": {
        "type": "apiKey",
        "in": "header",
        "name": "AuthToken"
    }
}

blobNamespace = Namespace('blob', 'Endpoints for managing blobs', authorizations=authorizations)


@blobNamespace.route('{blobId}')
class Blob(Resource):
    @blobNamespace.doc('list_todos')
    @blobNamespace.response(500, 'Internal Server error')
    @blobNamespace.response(200, 'Success')
    @blobNamespace.response(401, 'Unauthorized')
    @blobNamespace.response(403, 'Forbidden')
    @blobNamespace.response(404, 'Not found')
    @blobNamespace.doc(security='jsonWebToken')
    @blobNamespace.marshal_with(blob_model)

    def get(self):
        """Get a blob"""

        return "hello_world_example"
