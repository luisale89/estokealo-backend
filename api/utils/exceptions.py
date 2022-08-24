from email import message
from .responses import JSONResponse


class APIException(Exception, JSONResponse):

    def __init__(self, message, app_result="error", status_code=400, payload=None, warnings=None):  # default code 400
        Exception.__init__(self)
        JSONResponse.__init__(self, message, app_result, status_code, payload, warnings)

    @classmethod
    def from_response(cls, response:dict):
        '''creates an APIException object from an response message dict'''
        status_code = response.get("status_code", 400) # 400 is the default status code.
        msg = response.get("message", "general error")
        payload = response.get("payload", None)
        warnings = response.get("warnings", None)

        return cls(message=msg, status_code=status_code, payload=payload, warnings=warnings)