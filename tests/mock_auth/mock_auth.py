import os

from flask import Flask, jsonify
from dotenv import load_dotenv
app = Flask(__name__)

load_dotenv()

AUTH_PORT=os.getenv('AUTH_PORT', '3001')
AUTH_ADDRESS=os.getenv('AUTH_ADDRESS', '127.0.0.1')
@app.route('/api/v1/status', methods=['GET'])
def status():
    return '', 200

@app.route('/api/v1/user/<user>', methods=['GET'])
def user(user):
    if user == "USER":
        return '', 204
    else:
        return '', 404

@app.route('/api/v1/token/<token>', methods=['GET'])
def token(token):
    if token == "USER_TOKEN":
        return jsonify(user="USER"), 200
    else:
        return '', 404

if __name__ == '__main__':
    app.run(host=AUTH_ADDRESS, port=int(AUTH_PORT))