from typing import Union
from datetime import datetime, timezone
import os, re, string, unicodedata
from dateutil.parser import parse, ParserError
from itsdangerous import BadSignature, Signer
from random import sample
from flask_jwt_extended import create_access_token


def datetime_formatter(date:datetime) -> str:
    """
    returns a string that represents datetime stored in the database in UTC timezone
    datetime representation format: %Y-%m-%dT%H:%M:%S%z

    * Parameters
    <datetime> a valid datetime instance
    """
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_datetime(date:str) -> Union[datetime, None]:
    """
    Helper function to normalize datetime and store it into the database
    The normalized datetime is naive, and utc based
    """
    try:
        dt = parse(date)
        if dt.tzinfo is not None:
            date = dt.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            date = dt
    except ParserError:
        date = None

    return date


def convert_utc_epoch_to_datetime(epoch_utc:float) -> datetime:
    """
    Helper function to convert epoch timestamps into
    python datetime objects, in UTC
    Returns datetime in UTC format
    """
    return datetime.utcfromtimestamp(epoch_utc)


def create_qr_encoded_sign(payload:str) -> str:
    """sign a string using itsdangerous Signer class"""
    SECRET = os.environ["QR_SIGNER_SECRET"]
    QR_PREFIX = os.environ["QR_PREFIX"]
    signer = Signer(secret_key=SECRET)

    return signer.sign(f"{QR_PREFIX + payload}").decode("utf-8")


def read_qr_encoded_sign(qrcode:str) -> Union[str, None]:
    """
    decode data to
    get data inside a valid qrcode-signed string.

    returns the raw data inside the signed string.
    if the decode process fails, returns None
    """

    SECRET = os.environ["QR_SIGNER_SECRET"]
    QR_PREFIX = os.environ["QR_PREFIX"]
    signer = Signer(secret_key=SECRET)

    try:
        unsigned_core = signer.unsign(qrcode).decode("utf-8")
        return unsigned_core[len(QR_PREFIX):]

    except BadSignature:
        return None


def validate_inputs(inputs:dict) -> dict:
    """
    function to validate that there are no errors in the "inputs" dictionary
    Args:
        inputs (dict): inputs to validate following the format:
            {key: ('error':bool, 'msg':error message)}
        where key is the `key` of the field that is validating. example: email, password, etc.
        the output message will be the sum of all the individual messages separated by a |
    Returns dict:
        {key: error message}
    """
    invalids = {}

    for key, value in inputs.items():
        valid, msg = value
        if not valid:
            invalids.update({key: msg})

    return invalids


class StringHelpers:
    """StringHelpers utilities"""

    def __init__(self, value:str= "") -> None:
        self.value = value.strip() #remove blank spaces at the begining and the end of the word

    def __repr__(self) -> str:
        return f"StringHelpers(value={self.value})"

    def __str__(self) -> str:
        return f"{self.value!r}"

    def __bool__(self) -> bool:
        return True if self.value else False

    @property
    def as_normalized_email(self) -> str:
        """returns a string without blank spaces and lowercase"""
        return self.value.lower()

    @property
    def as_unaccent_word(self) -> str:
        """returns a string without accented characters
            -not receiving bytes as a string parameter-
        """ 
        nfkd_form = unicodedata.normalize('NFKD', self.value)
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


    def normalize(self, spaces:bool = False) -> str:
        """
        Normalize a characters string.
        Args:
            spaces (bool, optional): Indica si la cadena de caracteres incluye o no espacios. 
            Defaults to False.
        Returns:
            str: Candena de caracteres normalizada.
        """
        if not spaces:
            return self.value.replace(" ", "") #remove blank spaces inside the word
        else:
            return self.value
    

    def is_valid_string(self, max_length:int = 0) -> tuple[bool, str]:
        """
        function validates if a string is valid to be stored in the database.
        Args:
            max_length (int): max length of the string.
        Returns:
            (invalid:bool, str:error message)
        """
        if not self.value:
            return False, "empty string is an invalid value"

        if len(self.value) > max_length:
            return False, f"Input string is too long, {max_length} characters max."

        return True, "string validated"


    def is_valid_email(self) -> tuple[bool, str]:
        """
        Validates if a string has a valid email format
        Returns tuple:
            (valid:bool, str:error message)
                valid=True if the email is valid
                False if the email is invalid
        """
        max_length = 320
        if len(self.value) > max_length:
            return False, f"invalid email length, max is {max_length} chars"

        # Regular expression that checks a valid email
        ereg = '^[\w]+[\._]?[\w]+[@]\w+[.]\w{2,3}$'
        # ereg = '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        if not re.search(ereg, self.value):
            return False, f"invalid email format, <abc@def.gh> required"

        return True, "email is valid"


    def is_valid_password(self) -> tuple[bool, str]:
        """
        Check if a password meets the minimum security parameters
        defined for this application.
        Returns tuple:
            (invalid:bool, str:error message)
        """
        # Regular expression that checks a secure password
        preg = '^.*(?=.{8,})(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).*$'

        if not re.search(preg, self.value):
            return False, "password is invalid or not includes all required characters"

        return True, "password validated"


def is_valid_id(tar_int:int) -> tuple[bool, str]:
    """check if 'integer' parameter is a valid identifier value"""
    if not isinstance(tar_int, int) or tar_int < 0:
        return False, "parameter is not a valid identifier value, read documentation"

    return True, f"value [{tar_int}] is a valid indentifier"


def convert_str_to_int(tar_string:str) -> int:
    """Convierte una cadena de caracteres a su equivalente entero.
    Si la conversion no es válida, devuelve 0
    """
    if not isinstance(tar_string, str):
        return 0

    try:
        return int(tar_string)
    except Exception:
        return 0


def create_random_password(length:int = 16) -> str:
    """
    function creates a random password, default length is 16 characters.
    pass in required length as an integer parameter
    """
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    nums = string.digits
    symbols = string.punctuation

    all_cores = lower + upper + nums + symbols
    password = "".join(sample(all_cores, length))

    return password


class QueryParams:
    """class that represents the query parameters in request."""

    def __init__(self, params) -> None:
        self.params_flat = params.to_dict()
        self.params_non_flat = params.to_dict(flat=False)
        self.warnings = [] #each instance will be initialized with an empty list

    def __repr__(self) -> str:
        return f'QueryParams(params={self.params})'


    @staticmethod
    def _normalize_parameter(value:list):
        """
        Given a non-flattened query parameter value,
        and if the value is a list only containing 1 item,
        then the value is flattened.
        param value: a value from a query parameter
        return: a normalized query parameter value
        """
        return value if len(value) > 1 else value[0]


    def normalize_query(self) -> dict:
        """
        Converts query parameters from only containing one value for each parameter,
        to include parameters with multiple values as lists.
        :return: a dict of normalized query parameters
        """
        return {k: self._normalize_parameter(v) for k, v in self.params_non_flat.items()}


    def get_all_values(self, key:str) -> Union[list, None]:
        """return all values for specified key.
        return None if key is not found in the parameters
        """
        return self.params_non_flat.get(key, None)


    def get_first_value(self, key:str, as_integer:bool = False) -> Union[str, int, None]:
        """return first value in the list of specified key.
        return None if key is not found in the parameters
        """
        value = self.params_flat.get(key, None)
        if not value:
            self.warnings.append({key: f"{key} not found in query parameters"})
            return value

        if as_integer:
            int_value = convert_str_to_int(value)
            if not int_value:
                self.warnings.append({key: f"{value} can't be converted to 'int', is not a numeric string"})
            return int_value
        
        return value


    def get_all_integers(self, key:str) -> Union[list, None]:
        """returns a list of integers created from a list of values in the request. 
        if the conversion fails, the value is warnings
        > parameters: (key: str)
        > returns: values: [list || None]
        if no items was successfully converted to integer value, 
        an empty list is returned.
        """
        values = self.get_all_values(key)
        if not values:
            self.warnings.append({key: f"{key} not found in query parameters"})
            return None

        for v in values:
            if not isinstance(v, int):
                self.warnings.append({key: f"expecting 'int' value for [{key}] parameter, [{v}] was received"})

        return [int(v) for v in values if convert_str_to_int(v)]


    def get_pagination_params(self) -> tuple[int, int]:
        """
        function to get pagination parameters from request
        default values are given if no parameter is in request.
        Return Tuple -> (page, limit)
        """
        page = convert_str_to_int(self.params_flat.get("page", None))
        limit = convert_str_to_int(self.params_flat.get("limit", None))

        if not page:
            self.warnings.append({"page": "pagination parameter [page] not found as [int] in query string"})
            page = 1 #default page value
        if not limit:
            self.warnings.append({"limit": "pagination parameter [limit] not found as [int] in query string"})
            limit = 20 #default limit value

        return page, limit


    @staticmethod
    def get_pagination_form(pag_instance) -> dict:
        """
        Receive a pagination instance from flask-sqlalchemy,
        returns a dict with pagination data in a dict, set to return to the user.
        """
        return {
            "pagination": {
                "totalPages": pag_instance.pages,
                "hasNextPage": pag_instance.has_next,
                "hasPrevPage": pag_instance.has_prev,
                "currentPage": pag_instance.page,
                "totalItems": pag_instance.total
            }
        }


    def get_warings(self) -> dict:
        """returns query parameters feedback, including not found parameters
        or bad format parameters"""
        resp = {}
        for w in self.warnings:
            resp.update(w) if isinstance(w, dict) else resp.update({w: "error"})
        return {"queryParametersFeedback": resp}


def create_user_access_token(jwt_id:str, user_id:int) -> str:
    """
    Function that creates a jwt for the user.
    expected parameters:
    - jwt_id: identifier of the jwt. generally is the user email as string.
    - user_id: identifier of the user. this is the integer value stored in the database as pk.
    """
    return create_access_token(
        identity=jwt_id,
        additional_claims={
            "user_access_token": True,
            "user_id": user_id
        }
    )


def create_role_access_token(jwt_id:str, role_id:int, user_id:int) -> str:
    """
    Function that creates a jwt for the role.
    expected parameters:
    - jwt_id: identifier of the jwt. generally is the user email as string.
    - user_id: identifier of the user. this is the integer value stored in the database as pk.
    """
    return create_access_token(
        identity=jwt_id,
        additional_claims={
            "role_access_token": True,
            "user_access_token": True,
            "user_id": user_id,
            "role_id": role_id
        }
    )


def update_database_object(model:object, new_rows:dict) -> None:
    """
    update database table

    parameters
    - model (ORM instance to be updated)
    - new_rows:dict (new values)
    """
    for key, value in new_rows.items():
        setattr(model, key, value)
    
    return None