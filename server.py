from flask import Flask
from flask.wrappers import Response

app = Flask(__name__)


@app.route('/api/v1/')
def hello():
    return Response('Hola, its working', status=200)


app.run(debug=True)
