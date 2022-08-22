import os
from flask import Flask, request, abort
from sqlalchemy.exc import DBAPIError
from api.extensions import migrate, jwt, db, cors
from werkzeug.exceptions import HTTPException, InternalServerError


def create_app(test_config=None):
    app = Flask(__name__, static_folder=None)
    if test_config is None:
        app.config.from_object(os.environ["API_SETTINGS"])

    #init extensions
    db.init_app(app)
    migrate.init_app(app, db, directory=os.path.join(os.path.dirname(__file__), 'migrations'))
    jwt.init_app(app)
    cors.init_app(app)

    #API_ERROR_HANDLERS

    #API_BLUEPRINTS

    return app