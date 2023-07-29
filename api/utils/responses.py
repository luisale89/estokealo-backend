from flask import jsonify, Response


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
        message: str = "ok",
        result: str = "success",
        status_code: int = 200,
        data: dict = {},
    ) -> None:
        self.message = message
        self.result = result
        self.status_code = status_code
        self.data = data

    def __repr__(self) -> str:
        return (
            f"JSONResponse("
            f"message={self.message}, "
            f"result={self.result}, "
            f"status_code={self.status_code}"
            f"data={self.data})"
        )

    def serialize(self) -> dict:
        rv = {"message": self.message, "result": self.status_code, "payload": self.data}
        return rv

    def to_json(self) -> tuple[Response, int]:
        return jsonify(self.serialize()), self.status_code

    @staticmethod
    def bad_request(data: dict = None) -> dict:
        """status_code: 400"""
        status_code = 400
        return {
            "message": "bad request, check your inputs and try again",
            "result": status_code,
            "status_code": status_code,
            "data": {status_code: data},
        }

    @staticmethod
    def unauthorized(data: dict = None) -> dict:
        """status_code: 401"""
        status_code = 401
        return {
            "message": "user's authorization is invalid",
            "result": status_code,
            "status_code": status_code,
            "data": {status_code: data},
        }

    @staticmethod
    def user_not_active() -> dict:
        """status_code: 402"""
        status_code = 402
        return {
            "message": "user is not active or has not completed validation process",
            "result": status_code,
            "status_code": status_code,
        }

    @staticmethod
    def wrong_password() -> dict:
        """status_code: 403"""
        status_code = 403
        return {
            "message": "wrog password, check your inputs and try again",
            "result": status_code,
            "status_code": status_code,
        }

    @staticmethod
    def not_found(data: dict = {}) -> dict:
        """status_code: 404"""
        status_code = 404
        return {
            "message": "required resource was not found in the database",
            "result": status_code,
            "status_code": status_code,
            "data": {status_code: data},
        }

    @staticmethod
    def not_acceptable(data: dict = {}) -> dict:
        """status_code: 406"""
        status_code = 406
        return {
            "message": "invalid configuration in request parameters",
            "result": status_code,
            "status_code": status_code,
            "data": {status_code: data},
        }

    @staticmethod
    def conflict(data: dict = {}) -> dict:
        """status_code: 409"""
        status_code = 409
        return {
            "message": "data already exists in the database",
            "result": status_code,
            "status_code": status_code,
            "data": {status_code: data},
        }

    @staticmethod
    def permanently_deleted(data: dict = {}) -> dict:
        """status_code: 410"""
        result = "permanently_deleted"
        status_code = 410
        return {
            "message": "requested resource has been deleted",
            "result": status_code,
            "status_code": status_code,
            "data": {status_code: data},
        }

    @staticmethod
    def serivice_unavailable(data: dict = {}) -> dict:
        """status_code: 503"""
        result = "service_unavailable"
        status_code = 503
        return {
            "message": "requested service is unavailable, try again later",
            "result": status_code,
            "status_code": status_code,
            "data": {status_code: data},
        }
