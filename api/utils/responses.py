from flask import jsonify


class JSONResponse:
    """
    Genera mensaje de respuesta a las solicitudes JSON. los parametros son:
    - message: Mesanje a mostrar al usuario.
    - app_result = "success", "error"
    - status_code = http status code
    - payload = dict con cualquier informacion que se necesite enviar al usuario.
    - warnings = dict con las justificaciones de cada error detectado en el request.
    methods:
    - serialize() -> return dict
    - to_json() -> http JSON response
    """

    def __init__(self, message="ok", app_result="success", status_code=200, payload=None, warnings=None):
        self.app_result = app_result
        self.status_code = status_code
        self.data = payload
        self.message = message
        self.warings = warnings

    def __repr__(self) -> str:
        return f'JSONResponse(status_code={self.status_code})'

    def serialize(self):
        rv = {
            "result": self.app_result,
            "data": dict(self.data or ()),
            "message": self.message,
            "warings": dict(self.warings or ())
        }
        return rv

    def to_json(self):
        return jsonify(self.serialize()), self.status_code


class ErrorResponse:

    def __init__(self, parameters:list=None, warnings:dict=None) -> None:
        self.parameters = {"errors": parameters} #list of parameters with any error detected
        self.warnings = warnings
    
    def _base_response(self) -> dict:
        return {
            "message": "something went wrong, try again later",
            "status_code": 500,
            "payload": self.parameters or [],
            "warnings": self.warnings or {}
        }

    @property
    def bad_request(self) -> dict:
        return self._base_response().update({
            "message": "bad request, check your inputs and try again",
            "status_code": 400
        })

    @property
    def unauthorized(self) -> dict:
        return self._base_response().update({
            "message": "unauthorized to get requested resource",
            "status_code": 401
        })

    @property
    def user_not_active(self) -> dict:
        return self._base_response().update({
            "message": "user is not active or has not completed validation process"
        })

    @property
    def wrong_password(self) -> dict:
        return self._base_response().update({
            "message": "wrog password, check your input and try again",
            "status_code": 403
        })

    @property
    def not_found(self) -> dict:
        return self._base_response().update({
            "message": "resource was not found in the database",
            "status_code": 404
        })

    @property
    def unaccepted(self) -> dict:
        return self._base_response().update({
            "message": "invalid inputs were found in the request",
            "status_code": 406
        })

    @property
    def conflict(self) -> dict:
        return self._base_response().update({
            "message": "parameter already exists in the database",
            "status_code": 409
        })

    @property
    def service_unavailable(self) -> dict:
        return self._base_response().update({
            "message": "requested service is unavailable, try again later",
            "status_code": 503
        })