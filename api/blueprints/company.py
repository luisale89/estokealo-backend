from flask import Blueprint, request
from api.utils import helpers as h
from api.utils.responses import JSONResponse
from api.utils.exceptions import APIException
from api.utils.db_operations import handle_db_error, update_row_content, Unaccent
from api.utils.decorators import json_required, role_required
from api.services.email_service import Email_api_service as ems
from api.extensions import db
from api.models.main import Company, Role, User
from api.models.global_models import RoleFunction
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
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
    #filter 1
    if status: #["accepted", "rejected", "pending"]
        base_q = base_q.filter(Role._inv_status == status)

    all_roles = base_q.paginate(page, limit)

    return JSONResponse(
        data={
            "users": list(map(lambda x: {
                **x.user.serialize(),
                "role": x.serialize(),
                "role_function": x.role_function.serialize()
            }, all_roles.items)),
            **qp.get_pagination_form(all_roles),
            **qp.get_warings()
        }
    ).to_json()


@company_bp.route("/users/invitation", methods=["POST"])
@json_required({"email": str, "role_function_id": int})
@role_required(level=1)
def invite_user(role, body):

    email = h.StringHelpers(body["email"])
    role_function_id = body["role_function_id"]

    invalids = h.validate_inputs({
        "email": email.is_valid_email(),
        "role_function_id": h.is_valid_id(role_function_id)
    })
    if invalids:
        raise APIException.from_response(JSONResponse.bad_request(invalids))

    target_role_function = db.session.query(RoleFunction).filter(RoleFunction.id == role_function_id).first()
    if not target_role_function:
        raise APIException.from_response(JSONResponse.not_found({"role_function_id": role_function_id}))  

    if role.role_function.access_level > target_role_function.access_level:
        raise APIException.from_response(JSONResponse.unauthorized({"role": "invalid role access-level"}))

    target_user = db.session.query(User).filter(User._email == email.value).first()

    if not target_user:
        #user to invite does not exists in the app...
        success, msg = ems.user_invitation(
            email_to=email.email_normalized,
            company_name=role.company.name
        ).send_email()
        if not success:
            raise APIException.from_response(JSONResponse.serivice_unavailable(msg))

        try:
            new_user = User(
                email = email.email_normalized,
                password = h.StringHelpers.random_password(),
                signup_completed = False
            )
            new_role = Role(
                user = new_user,
                company_id = role.company.id,
                role_function = target_role_function
            )
            db.session.add_all(instances=[new_user, new_role])
            db.session.commit()
        except SQLAlchemyError as e:
            handle_db_error(e)

        return JSONResponse("new user invited", status_code=201).to_json()

    #if user exists
    rel_exists = db.session.query(User.id).join(User.roles).join(Role.company).\
        filter(User.id == target_user.id, Company.id == role.company.id).first()
    if rel_exists:
        raise APIException.from_response(JSONResponse.conflict({"email": email.value}))

    success, msg = ems.user_invitation(
        email_to=email.email_normalized,
        company_name=role.company.name,
        user_name=target_user.first_name
    ).send_email()
    if not success:
        raise APIException.from_response(JSONResponse.serivice_unavailable(msg))

    try:
        new_role = Role(
            company_id = role.company.id,
            user = target_user,
            role_function = target_role_function
        )
        db.session.add(new_role)
        db.session.commit()
    except SQLAlchemyError as e:
        handle_db_error(e)
    
    return JSONResponse("new user has been invited").to_json()


@company_bp.route("/users/<int:user_id>", methods=["PUT"])
@json_required({"is_active": bool})
@role_required(level=1)
def update_user_role(role, body:dict, user_id:int):

    invalid_id, msg_id = h.is_valid_id(user_id)
    if invalid_id:
        raise APIException.from_response(JSONResponse.bad_request({"user_id": msg_id}))

    target_role = db.session.query(Role).filter(Role.company_id == role.company.id).\
        filter(Role.user_id == user_id).first()
    if not target_role:
        raise APIException.from_response(JSONResponse.not_found({"user_id": user_id}))

    if role.id == target_role.id:
        raise APIException.from_response(JSONResponse.conflict({"role": "can't update self role"}))

    #update role status
    new_rows = {"is_active": body["is_active"]}

    #update role_function_id
    new_function_id = body.get("new_function_id", None)
    if new_function_id:
        invalid_id, msg_id = h.is_valid_id(new_function_id)
        if invalid_id:
            raise APIException.from_response(JSONResponse.bad_request({"new_function_id": new_function_id}))

        target_function = db.session.query(RoleFunction).get(new_function_id)
        if not target_function:
            raise APIException.from_response(JSONResponse.not_found({"new_function_id": new_function_id}))

        if role.access_level > target_function.access_level:
            raise APIException.from_response(JSONResponse.unauthorized({"role": "invalid role access-level"}))

        new_rows.update({"role_function_id": new_function_id})

    try:
        h.update_model(target_role, new_rows=new_rows)
        db.session.commit()

    except SQLAlchemyError as e:
        handle_db_error(e)
    
    return JSONResponse(
        message="role updated",
        data=target_role.serialize()
    ).to_json()


@company_bp.route("/users/<int:user_id>", methods=["DELETE"])
@json_required()
@role_required(level=1)
def delete_user_from_company(role, user_id):

    invalid, msg = h.is_valid_id(user_id)
    if invalid:
        raise APIException.from_response(JSONResponse.bad_request({"user_id": msg}))

    target_role = db.session.query(Role).filter(Role.company_id == role.company.id).\
        filter(Role.user_id == user_id).first()

    if not target_role:
        raise APIException.from_response(JSONResponse.not_found({"user_id": user_id}))

    if role.access_level > target_role.access_level:
        raise APIException.from_response(JSONResponse.unauthorized({"role": "invalid role access-level"}))

    try:
        db.session.delete(target_role)
        db.session.commit()

    except IntegrityError as ie:
        raise APIException.from_response(JSONResponse.conflict({"user": f"{ie}"}))

    except SQLAlchemyError as e:
        handle_db_error(e)

    return JSONResponse("Role has been deleted").to_json()


@company_bp.route('/roles', methods=['GET'])
@json_required()
@role_required()#any user
def get_company_roles(role):

    return JSONResponse(data={
        "roles": list(map(lambda x: x.serialize(), db.session.query(RoleFunction).all()))
    }).to_json()