import os
from flask import Flask
from sqlalchemy.exc import DBAPIError
from api.extensions import migrate, jwt, db, cors
from werkzeug.exceptions import HTTPException, InternalServerError
from api.utils.exceptions import APIException

from api.utils.responses import JSONResponse
from api.services.redis_service import RedisClient
#blueprints
from api.blueprints.v1 import auth


def create_app(test_config=None):
    app = Flask(__name__, static_folder=None)
    if test_config is None:
        app.config.from_object(os.environ["API_SETTINGS"])

    #API_ERROR_HANDLERS
    app.register_error_handler(HTTPException, handle_http_error)
    app.register_error_handler(APIException, handle_API_Exception)
    app.register_error_handler(InternalServerError, handle_internal_server_error)
    app.register_error_handler(DBAPIError, handle_DBAPI_disconnect)

    #init extensions
    db.init_app(app)
    migrate.init_app(app, db, directory=os.path.join(os.path.dirname(__file__), 'migrations'))
    jwt.init_app(app)
    cors.init_app(app)

    #API_BLUEPRINTS
    app.register_blueprint(auth.auth_bp, url_prefix="/v1/auth")

    return app


def handle_DBAPI_disconnect(e):
    resp = JSONResponse(JSONResponse.serivice_unavailable(data={
        "main_database": str(e)
    }))
    return resp.to_json()


def handle_http_error(e):
    return JSONResponse(
        message=e.description,
        status_code=e.code,
        app_result="http_error"
    ).to_json()


def handle_internal_server_error(e):
    resp = JSONResponse(
        message=e.description,
        status_code=500,
        app_result="error"
    )
    return resp.to_json()


def handle_API_Exception(exception):
    return exception.to_json()


#callbacks
@jwt.token_in_blocklist_loader #checks if a token is stored in the blocklist db
def check_if_token_revoked(jwt_header, jwt_payload) -> bool:
    jti = jwt_payload["jti"]
    rdb = RedisClient().set_connection()
    token_in_redis = rdb.get(jti)
    
    return token_in_redis is not None


@jwt.revoked_token_loader
@jwt.expired_token_loader
def expired_token_msg(jwt_header, jwt_payload):
    rsp = JSONResponse(JSONResponse.unauthorized(data={
        "jwt": "token has been revoked or has expired",
        "jwt_header": jwt_header,
        "jwt_payload": jwt_payload
    }))
    return rsp.to_json()


@jwt.invalid_token_loader
@jwt.unauthorized_loader
def invalid_token_msg(error):
    rsp = JSONResponse(JSONResponse.unauthorized(data={
        "jwt": error
    }))
    return rsp.to_json()