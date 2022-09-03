import os
from flask import Flask

def create_app(test_config=None):
    app = Flask(__name__, static_folder="build")
    if test_config is None:
        app.config.from_object(os.environ["FRONTEND_SETTINGS"])

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def catch_all(path):
        return app.send_static_file("index.html")

    return app