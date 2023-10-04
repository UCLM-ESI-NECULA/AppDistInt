"""REST Service"""

from flask import Flask, request
from flask.wrappers import Response

app = Flask(__name__)

STORAGE = []


@app.route('/api/v1/', methods=['GET'])
def hello():
    """Get service status"""
    return Response('Hola, its working', status=200)


@app.route('/api/v1/head/', methods=['GET'])
def get_head():
    try:
        head = STORAGE[-1]
    except IndexError:
        return Response("", status=204)
    return Response(head, status=200)


@app.route('/api/v1/head', methods=['PUT'])
def add_item():
    """Stack another item"""
    data = request.get_data(as_text=True)
    STORAGE.append(data)
    return Response(data, status=200)


@app.route('/api/v1/head/', methods=['DELETE'])
def remove_last_item():
    """Remove last item"""
    try:
        del STORAGE[-1]
    except IndexError:
        return Response("The Stack is empty", status=412)
    return Response("", status=204)


app.run(port=4999, debug=True)
