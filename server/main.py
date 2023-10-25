from flask import Flask
from controllers.init_cotroller import blueprint as basic_endpoints

app = Flask(__name__)
app.register_blueprint(basic_endpoints)
app.run(port=4999, debug=True)
if __name__ == "__main__":
    app.run()


