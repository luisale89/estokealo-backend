#python > 3.10
from api.utils.responses import JSONResponse, ResponseParams
from typing_extensions import Self


class APIException(Exception, JSONResponse):
    def __init__(
        self,
        exception_message: str,
        exception_status_code: int = 400,
    ) -> None:  # default code 400
        Exception.__init__(self)
        JSONResponse.__init__(self, message=exception_message, status_code=exception_status_code)

    @classmethod
    def from_response(cls, parameters: ResponseParams) -> Self:
        return cls(
            exception_message=parameters["message"],
            exception_status_code=parameters["status_code"]
        )