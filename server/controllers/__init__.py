from flask_restx import Api
from server.controllers.blob_controller import blobNamespace as hello_world_model

api = Api(
    title='Object Storage Service',
    version='1.0',
    description='API for managing blobs or byte packages.',

)


api.add_namespace(hello_world_model)
