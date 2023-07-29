from flask import jsonify, Response
from typing import TypedDict, Any


class ResponseParams(TypedDict, total=False):
    message: str
    status_code: int
    data: dict[str, Any]


class JSONResponse:
    """
    Genera mensaje de respuesta a las solicitudes JSON. los parametros son:
    - message: Mesanje a mostrar al usuario.
    - status_code = http status code
    - data = dict con cualquier informacion que se necesite enviar al usuario.
    methods:
    - serialize() -> return dict
    - to_json() -> http JSON response
    """

    def __init__(
        self,
        message: str = "success",
        status_code: int = 200,
        data: dict = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.data = data

    def __repr__(self) -> str:
        return (
            f"JSONResponse("
            f"message={self.message}, "
            f"status_code={self.status_code}"
            f"data={self.data})"
        )

    def serialize(self) -> dict:
        rv = {"message": self.message, "payload": self.data or {}}

        return rv

    def to_json(self) -> tuple[Response, int]:
        return jsonify(self.serialize()), self.status_code

    @staticmethod
    def bad_request() -> ResponseParams:
        """status_code: 400"""
        return {
            "message": "bad request, check your inputs and try again",
            "status_code": 400,
        }

    @staticmethod
    def unauthorized() -> ResponseParams:
        """status_code: 401"""
        return {
            "message": "invalid authorization in request",
            "status_code": 401,
        }

    @staticmethod
    def user_not_active() -> ResponseParams:
        """status_code: 402"""
        return {
            "message": "user is not active or have not completed registration process.",
            "status_code": 402,
        }

    @staticmethod
    def wrong_password() -> ResponseParams:
        """status_code: 403"""
        return {
            "message": "wrong password, check your inputs and try again",
            "status_code": 403
        }

    @staticmethod
    def not_found() -> ResponseParams:
        """status_code: 404"""
        return {
            "message": "required resources not found",
            "status_code": 404
        }

    @staticmethod
    def not_acceptable() -> ResponseParams:
        """status_code: 406"""
        return {
            "message": "invalid configuration in request parameters",
            "status_code": 406,
        }

    @staticmethod
    def conflict() -> ResponseParams:
        """status_code: 409"""
        return {
            "message": "data already exists in the database",
            "status_code": 409
        }

    @staticmethod
    def permanently_deleted() -> ResponseParams:
        """status_code: 410"""
        status_code = 410
        return {
            "message": "requested resource has been deleted",
            "status_code": 410,
        }

    @staticmethod
    def service_unavailable() -> ResponseParams:
        """status_code: 503"""
        return {
            "message": "the service is unavailable, try again later",
            "status_code": 503
        }