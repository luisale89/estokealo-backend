from flask import Blueprint, request
from api.utils import helpers as h
from api.utils.responses import JSONResponse
from api.utils.exceptions import APIException
from api.utils.db_operations import handle_db_error, update_row_content, Unaccent
from api.utils.decorators import json_required, user_required
from api.services.redis_service import RedisClient as rds
from api.extensions import db
from api.models.main import Company, Role, User
from api.models.global_models import RoleFunction
from flask_jwt_extended import get_jwt
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func


user_bp = Blueprint("user_pb", __name__)


@user_bp.route("/", methods=["GET"])
@json_required()
@user_required()
def get_user_info(user):
    '''return user info'''
    return JSONResponse(
        message="user profile",
        data=user.serialize_all()
    ).to_json()


@user_bp.route("/", methods=["PUT"])
@json_required()
@user_required()
def update_user_info(user, body):
    '''update user info'''
    newRows, invalids = update_row_content(User, body)
    if invalids:
        raise APIException.from_response(JSONResponse.bad_request(invalids))

    try:
        h.update_model(user, newRows)
        db.session.commit()
    except SQLAlchemyError as e:
        handle_db_error(e)

    return JSONResponse(
        message="user has been updated",
        data=user.serialize_all()
    ).to_json()


@user_bp.route("/companies", methods=["GET"])
@json_required()
@user_required()
def get_user_companies(user):
    '''get all user companies, from invitations and created'''
    qp = h.QueryParams(request.args)
    page, limit = qp.get_pagination_params()
    role_status = qp.get_first_value("status") #status: pending, accepted, rejected

    base_q = db.session.query(Role).filter(Role.user_id == user.id)
    #filter 1
    if role_status:
        base_q = base_q.filter(Role._inv_status == role_status)

    all_roles = base_q.paginate(page, limit)

    return JSONResponse(
        data={
            "companies": list(map(lambda x: {
                **x.company.serialize(),
                "role": x.serialize()
            }, all_roles.items)),
            **qp.get_pagination_form(all_roles),
            **qp.get_warings()
        }
    ).to_json()


@user_bp.route("/companies", methods=["POST"])
@json_required({"name": str})
@user_required()
def create_company(user, body):

    newRows, invalids = update_row_content(Company, body)
    if invalids:
        raise APIException.from_response(JSONResponse.bad_request(invalids))
    
    # #check if user has already a company under his name
    # owned_company = db.session.query(Company.id).select_from(User).join(User.roles).\
    #     join(Role.company).filter(User.id == user.id, Role.code == "owner").first()
    # if owned_company:
    #     raise APIException.from_response(JSONResponse.conflict(
    #         {"user": "user already has a company on his name"})
    #     )

    #check if name is available among all names in the app
    company_name = h.StringHelpers(newRows.get("name"))
    name_exists = db.session.query(Company.id).\
        filter(Unaccent(func.lower(Company.name)) == company_name.unaccent.lower()).first()
    if name_exists:
        raise APIException.from_response(JSONResponse.conflict(
            {"name": company_name.value}
        ))

    role_function = db.session.query(RoleFunction).filter(RoleFunction.code == "owner").first()
    if not role_function:
        role_function = RoleFunction.add_defaults("owner")

    try:
        new_company = Company(**newRows)
        new_role = Role(
            company = new_company,
            user = user,
            role_function = role_function,
            inv_status = "accepted"
        )
        db.session.add_all([new_company, new_role])
        db.session.commit()
    except SQLAlchemyError as e:
        handle_db_error(e)

    return JSONResponse(
        message="new company has been created",
        status_code=201,
        data=new_role.serialize_all()
    ).to_json()


@user_bp.route("/companies/<int:company_id>/invitation", methods=["PUT"])
@json_required({"accept_invitation": bool})
@user_required()
def update_role_status(user, body, company_id):

    inv_result = body["accept_invitation"]
    valid, msg = h.is_valid_id(company_id)
    if not valid:
        raise APIException.from_response(JSONResponse.bad_request(
            {"company_id": msg}
        ))

    target_role = db.session.query(Role).select_from(User).join(User.roles).\
        join(Role.company).filter(User.id == user.id, Company.id == company_id).first()

    if not target_role:
        raise APIException.from_response(JSONResponse.not_found(
            {"company_id": company_id}
        ))

    if not target_role.inv_status == "pending":
        raise APIException.from_response(JSONResponse.conflict(
            {"invitation": "already resolved"}
        ))

    if inv_result:
        target_role.inv_status = "accepted"
    else:
        target_role.inv_status = "rejected"

    db.session.commit()

    return JSONResponse(
        message="invitation resolved"
    ).to_json()


@user_bp.route("/companies/<int:company_id>/activate", methods=["GET"])
@json_required()
@user_required()
def get_company_access(user, company_id):

    valid, msg = h.is_valid_id(company_id)
    if not valid:
        raise APIException.from_response(JSONResponse.bad_request(
            {"company_id": msg}
        ))
    
    target_role = user.roles.filter(Role.company_id == company_id).first()
    if not target_role:
        raise APIException.from_response(JSONResponse.not_found(
            {"company_id": company_id}
        ))

    if not target_role.is_enabled:
        raise APIException.from_response(JSONResponse.user_not_active())

    rds().add_jwt_to_blocklist(get_jwt())
    access_token = h.create_role_access_token(
        jwt_id=user.email, 
        role_id=target_role.id, 
        user_id=user.id
    )

    return JSONResponse(
        message="company access granted",
        data={
            "access_token": access_token,
            **target_role.serialize_all()
        }
    ).to_json()