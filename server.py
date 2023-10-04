"""
    REST Service
"""

from flask import Flask
from flask.wrappers import Response

app = Flask(__name__)
STORAGE = []


@app.route('/api/v1/', methods=['GET'])
def hello():
    """
    Get service status
    """
    return Response('Hola, its working', status=200)


@app.route('/api/v1/head', methods=['GET'])
def get_head():
    try:
        head = STORAGE[-1]
    except IndexError:
        return Response("", status=204)
    return Response(head, status=200)


app.run(debug=True)
