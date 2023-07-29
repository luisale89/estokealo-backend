from flask import Blueprint, request
from api.utils import helpers as h
from api.utils.responses import JSONResponse
from api.utils.exceptions import APIException
from api.utils.db_operations import (
    handle_db_error,
    create_table_content,
    Unaccent,
    update_database_object,
)
from api.utils.decorators import json_required, user_required
from api.utils.enums import AccessLevel, OperationStatus
from api.services.redis_service import RedisClient as RDS
from api.extensions import db
from api.models.main import Company, Role, User
from flask_jwt_extended import get_jwt
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func


user_bp = Blueprint("user_pb", __name__)


@user_bp.route("/", methods=["GET"])
@user_required()
@json_required()
def get_user_info(user: User):
    """return user info"""
    response = {"user": user.serialize_all()}
    return JSONResponse(message="user profile", data=response).to_json()


@user_bp.route("/", methods=["PUT"])
@user_required()
@json_required(
    schema={
        "type": "object",
        "properties": User.SCHEMA_PROPS,
        "additionalProperties": False,
    }
)
def update_user_info(user, body):
    """update user info"""
    new_records, invalids = create_table_content(User, body)
    if invalids:
        raise APIException.from_response(JSONResponse.bad_request(invalids))

    try:
        update_database_object(user, new_records)
        db.session.commit()
    except SQLAlchemyError as e:
        handle_db_error(e)

    return JSONResponse(
        message="user has been updated", data=user.serialize_all()
    ).to_json()


@user_bp.route("/companies", methods=["GET"])
@user_required()
@json_required()
def get_user_companies(user):
    """get all user companies, from invitations or the ones that have been created"""
    qp = h.QueryParams(request.args)
    pg_params = qp.get_pagination_params()
    role_status = qp.get_first_value("status")  # status: pending, accepted, rejected

    base_q = db.session.query(Role).filter(Role.user_id == user.id)
    # filter 1
    if role_status:
        base_q = base_q.filter(Role._inv_status == role_status)

    all_roles = base_q.paginate(**pg_params)

    response = {
        "companies": list(map(lambda x: {**x.serialize_with_user()}, all_roles.items)),
        **qp.get_pagination_form(all_roles),
        **qp.get_warings(),
    }

    return JSONResponse(data=response).to_json()


@user_bp.route("/company", methods=["POST"])
@user_required()
@json_required(
    schema={
        "type": "object",
        "properties": Company.SCHEMA_PROPS,
        "required": ["name"],
        "additionalProperties": False,
    }
)
def create_company(user, body):
    new_records, invalids = create_table_content(Company, body)
    if invalids:
        raise APIException.from_response(JSONResponse.bad_request(invalids))

    # check if user has already a company under his name
    owned_company = (
        db.session.query(Company.id)
        .select_from(User)
        .join(User.roles)
        .join(Role.company)
        .filter(User.id == user.id, Role.access_level == AccessLevel.OWNER.value)
        .first()
    )
    if owned_company:
        raise APIException.from_response(
            JSONResponse.conflict({"user": "user already has a company on his name"})
        )

    # check if name is available among all names in the app
    company_name = new_records.get("name")
    name_exists = (
        db.session.query(Company.id)
        .filter(Unaccent(func.lower(Company.name)) == h.remove_accents(company_name))
        .first()
    )

    if name_exists:
        raise APIException.from_response(JSONResponse.conflict({"name": company_name}))

    try:
        new_company = Company(**new_records)
        new_role = Role(
            company=new_company,
            user=user,
            access_level=AccessLevel.OWNER.value,
            inv_status=OperationStatus.ACCEPTED.value,
        )
        db.session.add_all([new_company, new_role])
        db.session.commit()
    except SQLAlchemyError as e:
        handle_db_error(e)

    return JSONResponse(
        message="new company has been created",
        status_code=201,
        data=new_role.serialize_with_user(),
    ).to_json()


@user_bp.route("/companies/<int:company_id>/invitation", methods=["PUT"])
@user_required()
@json_required(
    schema={
        "type": "object",
        "properties": {
            "accept_invitation": {"type": "boolean"},
        },
        "required": ["accept_invitation"],
        "additionalProperties": False,
    }
)
def resolve_company_invitation(user, body, company_id):
    inv_result = body["accept_invitation"]
    valid, msg = h.is_valid_id(company_id)
    if not valid:
        raise APIException.from_response(JSONResponse.bad_request({"company_id": msg}))

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

    if not target_role.inv_status == "pending":
        raise APIException.from_response(
            JSONResponse.conflict({"invitation": "already resolved"})
        )

    if inv_result:
        target_role.inv_status = "accepted"
    else:
        target_role.inv_status = "rejected"

    db.session.commit()
    return JSONResponse(message="invitation resolved successfullt").to_json()


@user_bp.route("/companies/<int:company_id>/activate", methods=["GET"])
@json_required()
@user_required()
def get_company_access(user, company_id):
    valid, msg = h.is_valid_id(company_id)
    if not valid:
        raise APIException.from_response(JSONResponse.bad_request({"company_id": msg}))

    target_role: Role = user.roles.filter(Role.company_id == company_id).first()
    if not target_role:
        raise APIException.from_response(
            JSONResponse.not_found({"company_id": company_id})
        )

    if not target_role.is_enabled:
        raise APIException.from_response(JSONResponse.user_not_active())

    RDS().add_jwt_to_blocklist(get_jwt())
    access_token = h.create_role_access_token(
        jwt_id=user.email, role_id=target_role.id, user_id=user.id
    )

    response = {"access_token": access_token, "role": target_role.serialize_with_user()}

    return JSONResponse(message="company access granted", data=response).to_json()
