from flask import jsonify, Response

class JSONResponse:
    """
    Genera mensaje de respuesta a las solicitudes JSON. los parametros son:
    - message: Mesanje a mostrar al usuario.
    - result = "success", "error"
    - status_code = http status code
    - data = dict con cualquier informacion que se necesite enviar al usuario.
    methods:
    - serialize() -> return dict
    - to_json() -> http JSON response
    """

    def __init__(self, message="ok", result="success", status_code=200, data=None) -> None:
        self.message = message
        self.result = result
        self.status_code = status_code
        self.data = dict(data or ())

    def __repr__(self) -> str:
        return f"JSONResponse(" \
               f"message={self.message}, " \
               f"result={self.result}, " \
               f"status_code={self.status_code}" \
               f"data={self.data})"

    def serialize(self) -> dict:
        rv = {
            "message": self.message,
            "result": self.status_code,
            "payload": self.data
        }
        return rv

    def to_json(self) -> tuple[Response, int]:
        return jsonify(self.serialize()), self.status_code

    @staticmethod
    def bad_request(data:dict={}) -> dict:
        '''status_code: 400'''
        result = "bad_request"
        return {
            "message": "bad request, check your inputs and try again",
            "result": result,
            "status_code": 400,
            "data": {result: data}
        }

    @staticmethod
    def unauthorized(data:dict={}) -> dict:
        '''status_code: 401'''
        result = "unauthorized"
        return {
            "message": "user's authorization is invalid",
            "result": result,
            "status_code": 401,
            "data": {result: data}
        }

    @staticmethod
    def user_not_active() -> dict:
        '''status_code: 402'''
        return {
            "message": "user is not active or has not completed validation process",
            "result": "user_not_active",
            "status_code": 402,
        }

    @staticmethod
    def wrong_password() -> dict:
        '''status_code: 403'''
        return {
            "message": "wrog password, check your inputs and try again",
            "result": "wrong_password",
            "status_code": 403,
        }

    @staticmethod
    def not_found(data:dict={}) -> dict:
        '''status_code: 404'''
        status_code = 404
        return {
            "message": "required resource was not found in the database",
            "result": status_code,
            "status_code": status_code,
            "data": {status_code: data}
        }

    @staticmethod
    def not_acceptable(data:dict={}) -> dict:
        '''status_code: 406'''
        result = "not_acceptable"
        return {
            "message": "invalid configuration in request parameters",
            "result": result,
            "status_code": 406,
            "data": {result: data}
        }

    @staticmethod
    def conflict(data:dict={}) -> dict:
        '''status_code: 409'''
        result = "conflict"
        return {
            "message": "data already exists in the database",
            "result": result,
            "status_code": 409,
            "data": {result: data}
        }

    @staticmethod
    def permanently_deleted(data:dict={}) -> dict:
        '''status_code: 410'''
        result ="permanently_deleted"
        return {
            "message": "requested resource has been deleted",
            "result": result,
            "status_code": 410,
            "data": {result: data}
        }

    @staticmethod
    def serivice_unavailable(data:dict={}) -> dict:
        '''status_code: 503'''
        result = "service_unavailable"
        return {
            "message": "requested service is unavailable, try again later",
            "result": result,
            "status_code": 503,
            "data": {result: data}
        }