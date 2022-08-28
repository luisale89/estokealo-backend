from flask import Blueprint
from api.utils.responses import JSONResponse
from api.utils.exceptions import APIException
from api.extensions import db
from api.utils.decorators import json_required


auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/email-query", methods=["GET"])
@json_required()
def email_query():

    return JSONResponse("in development..").to_json()