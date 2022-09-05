import os
from flask import Flask, send_from_directory

def create_app(test_config=None):
    app = Flask(__name__, static_folder="build")
    if test_config is None:
        app.config.from_object(os.environ["FRONTEND_SETTINGS"])

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def catch_all(path):
        if path != "" and os.path.exists(app.static_folder + '/' + path):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

    return app