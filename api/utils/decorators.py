import functools
from flask import request, abort
from api.utils.exceptions import APIException
from api.models.main import User, Role
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from api.extensions import db
from api.utils.responses import JSONResponse
from jsonschema import validate
from jsonschema.exceptions import ValidationError


# decorator to be called every time an endpoint is reached
def json_required(schema: dict = {"type": "object"}):
    def decorator(func):
        @functools.wraps(func)
        def wrapper_func(*args, **kwargs):
            if not request.is_json:
                raise APIException.from_response(
                    JSONResponse.bad_request(data={
                        "request_header": "Missing 'content-type: application/json' in request header"
                    })
                )

            if request.method in ['PUT', 'POST']:  # body is present only in POST and PUT requests
                _json = request.get_json(silent=True)
                if not _json:
                    raise APIException.from_response(JSONResponse.bad_request(data="invalid json body in request"))
                try:
                    validate(instance=_json, schema=schema)
                except ValidationError as e:
                    message = " ".join(e.absolute_path) + ", " + e.message
                    raise APIException.from_response(JSONResponse.bad_request(data=message.strip()))

                kwargs['body'] = _json  # !
            return func(*args, **kwargs)

        return wrapper_func
    return decorator


# decorator to grant access to general users.
def role_required(level: int = 99):  # role-level required for the target endpoint
    def wrapper(fn):
        @functools.wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()

            if claims.get('role_access_token', None):
                role_id = claims.get('role_id', None)
                if not role_id:
                    abort(500, "role_id not present in jwt")

                role = db.session.query(Role).get(role_id)
                if role is None:
                    raise APIException.from_response(JSONResponse.permanently_deleted(data={
                        "role_id": f"role_id: {role_id} not found or has been deleted"
                    }))
                
                if not role.is_enabled or not role.user.is_enabled:
                    raise APIException.from_response(JSONResponse.user_not_active())

                if role.access_level > level:
                    raise APIException.from_response(JSONResponse.unauthorized(data={
                        "role_level": f"role_level must be less than {level} for this endpoint"
                    }))

                kwargs['role'] = role
                return fn(*args, **kwargs)
            else:
                raise APIException.from_response(JSONResponse.not_acceptable(data={
                    "jwt_claims": "'role_access_token' required"
                }))

        return decorator
    return wrapper


def user_required():
    def wrapper(fn):
        @functools.wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()

            if claims.get("user_access_token", False):
                user_id = claims.get('user_id', None)
                if not user_id:
                    abort(500, "user_id not present in jwt")

                user = db.session.query(User).get(user_id)
                if not user:
                    raise APIException.from_response(JSONResponse.permanently_deleted(data={
                        "user_id": f"user_id: {user_id} not found or has been deleted"
                    }))

                elif not user.is_enabled:
                    raise APIException.from_response(JSONResponse.user_not_active())

                kwargs['user'] = user
                return fn(*args, **kwargs)

            else:
                raise APIException.from_response(JSONResponse.not_acceptable(data={
                    "jwt_claims": "'user_access_token' required"
                }))

        return decorator
    return wrapper


# decorator to grant access to get user verifications.
def verification_token_required():
    def wrapper(fn):
        @functools.wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('verification_token', False):
                kwargs['claims'] = claims  # !
                return fn(*args, **kwargs)
            else:
                raise APIException.from_response(JSONResponse.not_acceptable(data={
                    "jwt_claims": "'verification_token' required"
                }))

        return decorator
    return wrapper


# decorator to grant access to verified users only.
def verified_token_required():
    def wrapper(fn):
        @functools.wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('verified_token', False):
                kwargs['claims'] = claims  # !
                return fn(*args, **kwargs)
            else:
                raise APIException.from_response(JSONResponse.not_acceptable(data={
                    "jwt_claims": "'verified_token' required"
                }))

        return decorator
    return wrapper