from datetime import timedelta
from random import randint
from flask import Blueprint, request
from api.utils import helpers as h
from api.utils.responses import JSONResponse
from api.utils.exceptions import APIException
from api.utils.db_operations import handle_db_error, update_row_content
from api.utils.decorators import json_required, user_required, verification_token_required, verified_token_required
from api.services.email_service import Email_api_service as ems
from api.services.redis_service import RedisClient as rds
from api.extensions import db
from api.models.main import Company, Role, User
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, get_jwt


auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/email-public-info", methods=["GET"])
@json_required()
def get_email_public_info():
    '''public endpoint'''
    qp = h.QueryParams(request.args)
    email = h.StringHelpers(qp.get_first_value("email"))

    if not email:
        raise APIException.from_response(JSONResponse.bad_request(qp.get_warings()))

    valid, msg = email.is_valid_email()
    if not valid:
        raise APIException.from_response(JSONResponse.bad_request({"email": msg}))

    user = db.session.query(User).filter(User._email == email.email_normalized, User._signup_completed == True).first()
    if not user:
        raise APIException.from_response(JSONResponse.not_found({"email": email.core}))

    return JSONResponse(data={
        **user.serialize_public_info()
    }).to_json()


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
    email = h.StringHelpers(qp.get_first_value("email"))

    if not email:
        raise APIException.from_response(JSONResponse.bad_request(qp.get_warings()))

    valid, msg = email.is_valid_email()
    if not valid:
        raise APIException.from_response(JSONResponse.bad_request({"email": msg}))

    random_code = randint(100000, 999999)
    success, msg = ems.user_verification(email_to=email.core, verification_code=random_code).send_email()
    if not success:
        raise APIException.from_response(JSONResponse.serivice_unavailable({"email_serivice": msg}))

    verification_token = create_access_token(
        identity=email.email_normalized,
        expires_delta=timedelta(hours=4), #verification token expiration datetime
        additional_claims={
            "verification_code": random_code,
            "verification_token": True
        }
    )

    return JSONResponse(
        message="verification code sent to user",
        data={
            "email": email.email_normalized,
            "verification_token": verification_token
        }
    ).to_json()


@auth_bp.route("/email-validation", methods=["PUT"])
@json_required({"verification_code": int})
@verification_token_required()
def validate_verification_code(claims, body):

    if body["verification_code"] != claims.get("verification_code"):
        raise APIException.from_response(JSONResponse.bad_request({"verification_code": "invalid code"}))
    email_in_claims = claims["sub"]
    #jwt to blocklist
    rds().add_jwt_to_blocklist(claims)

    user = db.session.query(User).filter(User._email == email_in_claims).first()
    verified_token = create_access_token(
        identity=email_in_claims,
        additional_claims={
            "verified_token": True
        }
    )
    payload = {
        "verified_token": verified_token
    }
    if user:
        payload.update({**user.serialize()})

    return JSONResponse(
        "verification process successfully completed",
        data=payload
    ).to_json()


@auth_bp.route("/signup", methods=["POST", "PUT"])
@json_required({"password": str, "first_name": str, "last_name": str})
@verified_token_required()
def signup_user(body, claims):

    email = claims.get("sub")
    password = h.StringHelpers(body["password"])
    invalids = h.validate_inputs({
        "password": password.is_valid_pw()
    })
    newRows, invalid_body = update_row_content(User, body)
    invalids.update(invalid_body)
    if invalids:
        raise APIException.from_response(JSONResponse.bad_request(invalids))

    newRows.update({
        "email": email,
        "password": password.core,
        "signup_completed": True
    })
    #jwt to blocklist
    rds().add_jwt_to_blocklist(claims)
    user = db.session.query(User).filter(User._email == email).first()
    #complete user's registration process
    if request.method == "PUT":
        if not user:
            raise APIException.from_response(JSONResponse.not_found({"email": email}))

        if user.signup_completed:
            raise APIException.from_response(JSONResponse.conflict({"email": email}))

        try:
            h.update_model(user, newRows)
            db.session.commit()
        except SQLAlchemyError as e:
            handle_db_error(e)

        access_token = h.create_user_access_token(jwt_id=user.email, user_id=user.id)

        return JSONResponse(
            message="user has completed signup process",
            data={**user.serialize_all(), "access_token": access_token}
        ).to_json()

    #if request.method == "POST"
    if user: #if user already exists in the database
        raise APIException.from_response(JSONResponse.conflict({"email": email}))

    new_user = User(**newRows)
    try:
        db.session.add(new_user)
        db.session.commit()
    except SQLAlchemyError as e:
        handle_db_error(e)

    access_token = h.create_user_access_token(jwt_id=new_user.email, user_id=new_user.id)

    return JSONResponse(
        message="new user has been created",
        status_code=201,
        data={
            **new_user.serialize_all(),
            "access_token": access_token
        }
    ).to_json()


@auth_bp.route("/password-reset", methods=["PUT"])
@json_required({"new_password": str, "re_new_password": str})
@verified_token_required()
def reset_user_password(body, claims):

    email = claims.get("sub")
    new_password = h.StringHelpers(body["new_password"])
    re_new_password = body["re_new_password"]

    if not new_password.value == re_new_password:
        raise APIException.from_response(
            JSONResponse.bad_request({"re_new_password": "no match between passwords"})
        )

    valid, msg = new_password.is_valid_pw()
    if not valid:
        raise APIException.from_response(JSONResponse.bad_request({"new_password": msg}))

    #jwt to blocklist
    rds().add_jwt_to_blocklist(claims)
    
    user = db.session.query(User).filter(User._email == email).first()
    if not user:
        raise APIException.from_response(JSONResponse.not_found({"email": email}))

    try:
        user.password = new_password.value
        db.session.commit()
    except SQLAlchemyError as e:
        handle_db_error(e)

    return JSONResponse(message="user password has been updated").to_json()


@auth_bp.route("/login", methods=["POST"])
@json_required({"email": str, "password": str})
def login_user(body):

    email = h.StringHelpers(body["email"])
    password = h.StringHelpers(body["password"])
    invalids = h.validate_inputs({
        "email": email.is_valid_email(),
        "password": password.is_valid_pw()
    })
    if invalids:
        raise APIException.from_response(JSONResponse.bad_request(invalids))

    user = db.session.query(User).filter(User._email == email.email_normalized).first()
    if not user:
        raise APIException.from_response(JSONResponse.not_found({"email": email}))

    if not user.is_enabled:
        raise APIException.from_response(JSONResponse.user_not_active())

    if not check_password_hash(user._password_hash, password.value):
        raise APIException.from_response(JSONResponse.wrong_password())

    payload = {
        **user.serialize(),
        "access_token": h.create_user_access_token(jwt_id=email.email_normalized, user_id=user.id)
    }

    #if login want to be done including a specific role
    company_id = body.get("company_id", None)
    if company_id: #login with company
        valid, msg = h.is_valid_id(company_id)
        if not valid:
            raise APIException.from_response(JSONResponse.bad_request(
                {"company_id": msg}
            ))

        target_role = db.session.query(Role).select_from(User).\
            join(User.roles).join(Role.company).filter(User.id == user.id, Company.id == company_id).first()
        
        if not target_role:
            raise APIException.from_response(JSONResponse.not_found(
                {"company_id": company_id}
            ))

        if not target_role.is_enabled:
            raise APIException.from_response(JSONResponse.user_not_active())

        payload.update({
            "access_token": h.create_role_access_token(
                jwt_id=user.email, 
                role_id=target_role.id,
                user_id=user.id
            ),
            **target_role.company.serialize()
        })

    return JSONResponse(
        message="user logged in",
        data=payload
    ).to_json()


@auth_bp.route("/logout", methods=["DELETE"])
@json_required()
@user_required()
def logout_user(user):

    rds().add_jwt_to_blocklist(get_jwt())
    return JSONResponse(f"user {user.email!r} has been logged out").to_json()