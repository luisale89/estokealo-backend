import os
from flask import Flask, render_template
from .extensions import assets


def create_app(test_config=None):
    app = Flask(__name__)
    if test_config is None:
        app.config.from_object(os.environ["LANDINGPAGE_SETTINGS"])

    assets.init_app(app)

    @app.route("/")
    def index():
        print(app.config["DEVELOPMENT"])
        return render_template("index.html")

    return app