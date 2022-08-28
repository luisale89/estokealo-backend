from email import message
from unittest import result
from .responses import JSONResponse


class APIException(Exception, JSONResponse):

    def __init__(self, *args, **kwargs):  # default code 400
        Exception.__init__(self)
        super().__init__(*args, **kwargs)

    @classmethod
    def from_response(cls, response:dict):
        return cls(
            message=response.get("message", "something went wrong..."),
            result=response.get("result", "internal_server_error"),
            status_code=response.get("status_code", 500),
            data=response.get("data", None)
        )