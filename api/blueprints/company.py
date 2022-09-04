from crypt import methods
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