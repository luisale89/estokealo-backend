from flask import jsonify


class JSONResponse:
    """
    Genera mensaje de respuesta a las solicitudes JSON. los parametros son:
    - message: Mesanje a mostrar al usuario.
    - app_result = "success", "error"
    - status_code = http status code
    - payload = dict con cualquier informacion que se necesite enviar al usuario.
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
    ''''''
    BAD_REQUEST= "bad request, check inputs and try again", 400
    UNAUTHORIZED= "user is not authorized to get the resource", 401
    USER_NOT_ACTIVE= "user is not active or has been disabled", 402
    WRONG_PASSWOTD= "wrog password, try again", 403
    NOT_FOUND= "requested resource was not found in the database", 404
    NOT_ACCEPTABLE= "invalid inputs were found in the request body", 406
    CONFLICT= "parameter already exists in the database", 409
    SERVICE_UNAVAILABLE= "requested service is unavailable, try again later", 503

    def __init__(self, parameters:dict={}) -> None:
        self.parameters = parameters