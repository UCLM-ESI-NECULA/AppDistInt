from flask import Blueprint, request, Response

blueprint = Blueprint('api', __name__, url_prefix='/api/v1')


@blueprint.route('', methods=['GET'])
def hello():
    """Get service status"""
    return Response('Hi, its working', status=200)
