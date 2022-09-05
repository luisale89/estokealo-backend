from flask import Blueprint, request
from api.utils import helpers as h
from api.utils.responses import JSONResponse
from api.utils.exceptions import APIException
from api.utils.db_operations import handle_db_error, update_row_content, Unaccent
from api.utils.decorators import json_required, role_required, user_required
from api.extensions import db
from api.models.main import Company, Role, User
from api.models.global_models import RoleFunction
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func


company_bp = Blueprint("company_bp", __name__)


@company_bp.route("/", methods=["GET"])
@json_required()
@role_required()
def get_company(role):

    return JSONResponse(
        data= role.company.serialize_all()
    ).to_json()


@company_bp.route("/", methods=["PUT"])
@json_required()
@role_required(level=1)
def update_company(role, body):

    newRows, invalids = update_row_content(Company, body)
    if invalids:
        raise APIException.from_response(JSONResponse.bad_request(invalids))

    if "name" in newRows:
        company_name = h.StringHelpers(newRows.get("name"))
        name_exists = db.session.query(Company.id).\
            filter(Unaccent(func.lower(Company.name)) == company_name.unaccent.lower()).\
                filter(Company.id != role.company.id).first()

        if name_exists:
            raise APIException.from_response(JSONResponse.conflict(
                {"name": company_name.value}
            ))

    try:
        h.update_model(role.company, newRows)
        db.session.commit()
    except SQLAlchemyError as e:
        handle_db_error(e)

    return JSONResponse(
        message="company has been updated",
        data=role.company.serialize_all()
    ).to_json()


@company_bp.route("/users", methods=["GET"])
@json_required()
@role_required(level=1)
def get_company_users(role):

    qp = h.QueryParams(request.args)
    status = qp.get_first_value("status")
    page, limit = qp.get_pagination_params()

    base_q = db.session.query(Role).join(Role.company).filter(Company.id == role.company.id)
    #filter #1
    if status: #["accepted", "rejected", "pending"]
        base_q = base_q.filter(Role._inv_status == status)

    all_roles = base_q.paginate(page, limit)

    return JSONResponse(
        data={
            "users": list(map(lambda x: {
                **x.serialize(),
                **x.user.serialize(),
                **x.role_function.serialize()
            }, all_roles.items)),
            **qp.get_pagination_form(all_roles),
            **qp.get_warings()
        }
    ).to_json()


@company_bp.route("/users/invitation", methods=["POST"])
@json_required()
@role_required(level=1)
def create_user_invitation(role, body):

    return JSONResponse("in development...").to_json()


@company_bp.route("/users/<int:user_id>", methods=["PUT"])
@json_required()
@role_required(level=1)
def update_user_role(role, body):

    return JSONResponse("in development...").to_json()


@company_bp.route("/users/<int:user_id>", methods=["DELETE"])
@json_required()
@role_required(level=1)
def delete_user_from_company(role):

    return JSONResponse("in development...").to_json()


@company_bp.route('/roles', methods=['GET'])
@json_required()
@role_required()#any user
def get_company_roles(role):

    return JSONResponse(data={
        "roles": list(map(lambda x: x.serialize(), db.session.query(RoleFunction).all()))
    }).to_json()