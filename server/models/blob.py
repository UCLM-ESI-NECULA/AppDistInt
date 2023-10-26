from flask_restx import fields

from ..controllers import api

acl_model = api.model("acl", {
    "user": fields.String(required=False),
    "allowed_users": fields.List(fields.String, required=False),
})

blob_model = api.model("blob", {
    "blobId": fields.String(required=True),
    "url": fields.List(fields.String, required=True),
})
