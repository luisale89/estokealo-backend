from email import message
from unittest import result
from .responses import JSONResponse


class APIException(Exception, JSONResponse):
    def __init__(
        self,
        message: str,
        result: str = "error",
        status_code: int = 400,
        data: dict = {},
    ) -> None:  # default code 400
        Exception.__init__(self)
        JSONResponse.__init__(self, message, result, status_code, data)

    @classmethod
    def from_response(cls, response: dict) -> object:
        return cls(
            message=response.get("message", "something went wrong..."),
            result=response.get("result", "internal_server_error"),
            status_code=response.get("status_code", 500),
            data=response.get("data", {}),
        )
