from datetime import timedelta
from random import randint
from flask import Blueprint, request
from api.utils import helpers as h
from api.utils.responses import JSONResponse
from api.utils.exceptions import APIException
from api.utils.db_operations import (
    handle_db_error,
    create_table_content,
    update_database_object,
)
from api.utils.decorators import (
    json_required,
    user_required,
    verification_token_required,
    verified_token_required,
)
from api.services.email_service import Email_api_service as Email
from api.services.redis_service import RedisClient as Redis
from api.extensions import db
from api.models.main import Company, Role, User
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, get_jwt


auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/user-public-info", methods=["GET"])
@json_required()
def get_user_public():
    """Public Endpoint"""
    qp = h.QueryParams(request.args)
    email = qp.get_first_value("email")

    if not email:  # if email is not in query parameters
        raise APIException.from_response(JSONResponse.bad_request())

    valid, msg = h.is_valid_email_format(email)
    if not valid:
        raise APIException.from_response(JSONResponse.bad_request())

    user = User.filter_user_by_email(email=h.normalize_string(email))
    if not user or not user.signup_completed:
        raise APIException.from_response(JSONResponse.not_found())

    return JSONResponse(data={"user_public": user.serialize_public_info()}).to_json()


@auth_bp.route("/email-validation", methods=["GET"])
@json_required()
def get_email_validationCode():
    """
    * PUBLIC ENDPOINT *
    Endpoint to request a new verification code to validate that email really exists
    required in query params:
        ?email="valid-email:str"
    """
    qp = h.QueryParams(request.args)
    email = qp.get_first_value("email")

    if not email:
        raise APIException.from_response(JSONResponse.bad_request(qp.get_warings()))

    valid, msg = h.is_valid_email_format(email)
    if not valid:
        raise APIException.from_response(JSONResponse.bad_request({"email": msg}))

    normalized_email = h.normalize_string(email)

    random_code = randint(100000, 999999)
    success, msg = Email.user_verification(
        email_to=normalized_email, verification_code=random_code
    ).send_email()
    if not success:
        raise APIException.from_response(
            JSONResponse.service_unavailable({"email_serivice": msg})
        )

    verification_token = create_access_token(
        identity=normalized_email,
        expires_delta=timedelta(hours=4),  # verification token expiration datetime
        additional_claims={
            "verification_code": random_code,
            "verification_token": True,
        },
    )
    return JSONResponse(
        message="verification code sent to user",
        data={"verification_token": verification_token},
    ).to_json()


@auth_bp.route("/email-validation", methods=["PUT"])
@verification_token_required()
@json_required(
    schema={
        "type": "object",
        "properties": {
            "verification_code": {
                "type": "integer",
                "minimum": 100000,
                "maximum": 999999,
            }
        },
        "required": ["verification_code"],
        "additionalProperties": False,
    }
)
def validate_verification_code(claims, body):
    if body["verification_code"] != claims.get("verification_code"):
        raise APIException.from_response(
            JSONResponse.bad_request({"verification_code": "invalid code"})
        )

    email_in_claims = claims["sub"]
    Redis().add_jwt_to_blocklist(claims)  # jwt to blocklist
    verified_token = create_access_token(
        identity=email_in_claims, additional_claims={"verified_token": True}
    )

    return JSONResponse(
        "verification process successfully completed",
        data={"verified_token": verified_token},
    ).to_json()


@auth_bp.route("/signup", methods=["POST"])
@verified_token_required()
@json_required(
    schema={
        "type": "object",
        "properties": {
            "password": {"type": "string"},
            "re_password": {"type": "string"},
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
        },
        "required": ["password", "re_password", "first_name", "last_name"],
        "additionalProperties": False,
    }
)
def signup_user(body, claims):
    email = claims.get("sub")
    password = body["password"]
    re_password = body["re_password"]
    # test inputs
    invalids = h.validate_inputs({"password": h.is_valid_password_format(password)})
    new_records, invalid_records = create_table_content(User, body)
    invalids.update(invalid_records)

    if not password == re_password:
        invalids.update({"re_password": "no match between passwords"})

    if invalids:
        raise APIException.from_response(JSONResponse.bad_request(data=invalids))

    new_records.update({"email": email, "password": password, "signup_completed": True})
    # jwt to blocklist
    Redis().add_jwt_to_blocklist(claims)
    user: User = User.filter_user_by_email(email=email)
    response = {"access_token": ""}
    # complete user's registration process
    if user:
        if user.signup_completed:
            raise APIException.from_response(
                JSONResponse.conflict({"email": email})
            )  # responds with a 409 status

        try:
            update_database_object(user, new_records)
            db.session.commit()
        except SQLAlchemyError as e:
            handle_db_error(e)

        access_token = h.create_user_access_token(jwt_id=user.email, user_id=user.id)
        response.update({"access_token": access_token, "user": user.serialize_all()})
        return JSONResponse(
            message="user has completed signup process", status_code=201, data=response
        ).to_json()

    # if user is None, create new user
    new_user = User(**new_records)
    try:
        db.session.add(new_user)
        db.session.commit()
    except SQLAlchemyError as e:
        handle_db_error(e)

    access_token = h.create_user_access_token(
        jwt_id=new_user.email, user_id=new_user.id
    )
    response.update({"access_token": access_token, "user": new_user.serialize_all()})

    return JSONResponse(
        message="new user has been created", status_code=201, data=response
    ).to_json()


@auth_bp.route("/password-reset", methods=["PUT"])
@verified_token_required()
@json_required(
    schema={
        "type": "object",
        "properties": {
            "new_password": {"type": "string"},
            "re_password": {"type": "string"},
        },
        "required": ["new_password", "re_password"],
        "additionalProperties": False,
    }
)
def reset_user_password(body, claims):
    email = claims.get("sub")
    new_password = body["new_password"]
    re_new_password = body["re_password"]

    valid, msg = h.is_valid_password_format(new_password)
    if not valid:
        raise APIException.from_response(
            JSONResponse.bad_request({"new_password": msg})
        )

    if not new_password == re_new_password:
        raise APIException.from_response(
            JSONResponse.bad_request({"re_new_password": "no match between passwords"})
        )

    # jwt to blocklist
    Redis().add_jwt_to_blocklist(claims)

    user: User = User.filter_user_by_email(email=email)
    if not user:
        raise APIException.from_response(JSONResponse.not_found({"email": email}))

    try:
        user.password = new_password
        db.session.commit()
    except SQLAlchemyError as e:
        handle_db_error(e)

    return JSONResponse(message="user password has been updated").to_json()


@auth_bp.route("/login", methods=["POST"])
@json_required(
    schema={
        "type": "object",
        "properties": {
            "email": {"type": "string"},
            "password": {"type": "string"},
            "company_id": {"type": "integer", "minimum": 1},
        },
        "required": ["email", "password"],
        "additionalProperties": False,
    }
)
def login_user(body):
    email = body["email"]
    password = body["password"]
    # test inputs
    invalids = h.validate_inputs(
        {
            "email": h.is_valid_email_format(email),
            "password": h.is_valid_password_format(password),
        }
    )
    if invalids:
        raise APIException.from_response(JSONResponse.bad_request(invalids))

    normalized_email = h.normalize_string(email)

    user: User = User.filter_user_by_email(email=normalized_email)
    if not user:
        raise APIException.from_response(
            JSONResponse.not_found({"email": normalized_email})
        )

    if not user.is_enabled:
        raise APIException.from_response(JSONResponse.user_not_active())

    if not check_password_hash(user.password, password):
        raise APIException.from_response(JSONResponse.wrong_password())

    response = {
        "access_token": h.create_user_access_token(
            jwt_id=normalized_email, user_id=user.id
        ),
        "user": user.serialize_all(),
    }

    # if login needs to be done including a specific role
    company_id = body.get("company_id", None)
    if company_id:  # login with company
        target_role: Role = (
            db.session.query(Role)
            .select_from(User)
            .join(User.roles)
            .join(Role.company)
            .filter(User.id == user.id, Company.id == company_id)
            .first()
        )

        if not target_role:
            raise APIException.from_response(
                JSONResponse.not_found({"company_id": company_id})
            )

        if not target_role.is_enabled:
            raise APIException.from_response(JSONResponse.user_not_active())

        response.update(
            {
                "access_token": h.create_role_access_token(
                    jwt_id=user.email, role_id=target_role.id, user_id=user.id
                ),
                "role": target_role.serialize_with_user(),
            }
        )

    return JSONResponse(
        message=f"user {user.email!r} logged in", data=response
    ).to_json()


@auth_bp.route("/logout", methods=["DELETE"])
@user_required()
@json_required()
def logout_user(user):
    Redis().add_jwt_to_blocklist(get_jwt())
    return JSONResponse(f"user {user.email!r} has been disconected").to_json()


@auth_bp.route("/test-jwt", methods=["GET"])
@user_required()
@json_required()
def test_user_validation(user: User):
    response = {
        "user": user.serialize_all(),
    }
    claims = get_jwt()

    if claims.get("role_id", False):
        target_role: Role = (
            db.session.query(Role).filter(Role.id == claims["role_id"]).first()
        )
        response.update({"role": target_role.serialize_with_user()})

    return JSONResponse(
        f"token for user: {user.email!r} is valid", data=response
    ).to_json()
