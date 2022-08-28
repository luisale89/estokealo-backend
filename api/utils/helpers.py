from typing import Union
from datetime import datetime, timezone
import os, re, string, unicodedata
from dateutil.parser import parse, ParserError
from itsdangerous import BadSignature, Signer
from random import sample


def datetime_formatter(date:datetime) -> str:
    '''
    returns a string that represents datetime stored in the database in UTC timezone
    datetime represetnation format: %Y-%m-%dT%H:%M:%S%z

    * Parameters
    <datetime> a valid datetime instance
    '''
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_datetime(date:datetime) -> Union(datetime, None):
    '''
    Helper function to normalize datetime and store it into the database
    The normalized datetime is naive, and utc based
    '''
    try:
        dt = parse(datetime)
        if dt.tzinfo is not None:
            date = dt.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            date = dt
    except ParserError:
        date = None

    return date


def epoch_utc_to_datetime(epoch_utc:str) -> datetime:
    '''
    Helper function to convert epoch timestamps into
    python datetime objects, in UTC
    '''
    return datetime.utcfromtimestamp(epoch_utc)


def qr_encoder(payload:str) -> str:
    '''sign a string using itsdangerous Signer class'''
    SECRET = os.environ.get("QR_SIGNER_SECRET")
    QR_PREFIX = os.environ.get("QR_PREFIX")
    signer = Signer(secret_key=SECRET)

    return signer.sign(f"{QR_PREFIX + payload}").decode("utf-8")


def qr_decoder(qrcode:str) -> Union[str, None]:
    '''
    decode data to 
    get data inside a valid qrcode-signed string.

    returns the raw data inside the signed string.
    if the decode process fails, returns None
    '''

    SECRET = os.environ.get("QR_SIGNER_SECRET")
    QR_PREFIX = os.environ.get("QR_PREFIX")
    signer = Signer(secret_key=SECRET)

    try:
        unsigned_core = signer.unsign(qrcode).decode("utf-8")
        return unsigned_core[len(QR_PREFIX):]

    except BadSignature:
        return None


def is_valid_id(tar_int:int) -> tuple:
    """check if 'integer' parameter is a valid identifier value"""
    if not isinstance(tar_int, int) or tar_int < 0:
        return False, "parameter is not a valid identifier value, read documentation"
    
    return True, f"value [{tar_int}] is a valid indentifier"


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

    def __init__(self, string:str=None) -> None:
        self._string = string or ""

    def __repr__(self) -> str:
        return f"StringHelpers(string:{self.string})"

    def __bool__(self) -> bool:
        return True if self.string else False

    @property
    def string(self) -> str:
        return self._string
    
    @string.setter
    def string(self, new_val:str):
        self._string = new_val if isinstance(new_val, str) else ''

    @property
    def core(self) -> str:
        """returns string without blank spaces at the begining and the end"""
        return self.string.strip()

    @property
    def email_normalized(self) -> str:
        return self.core.lower()

    @property
    def unaccent(self) -> str:
        """returns a string without accented characters
            -not receiving bytes as a string parameter-
        """ 
        nfkd_form = unicodedata.normalize('NFKD', self.core)
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
    

    @staticmethod
    def to_int(tar_string:str) -> int:
        """Convierte una cadena de caracteres a su equivalente entero.
        Si la conversion no es válida, devuelve 0
        """
        if not isinstance(tar_string, str):
            return 0

        try:
            return int(tar_string)
        except Exception:
            return 0


    def normalize(self, spaces:bool = False) -> str:
        """
        Normalize a characters string.
        Args:
            target_string (str): cadena de caracteres a normalizar.
            spaces (bool, optional): Indica si la cadena de caracteres incluye o no espacios. 
            Defaults to False.
        Returns:
            str: Candena de caracteres normalizada.
        """
        if not spaces:
            return self.core.replace(" ", "")
        else:
            return self.core
    

    def is_valid_string(self, max_length: int = None) -> tuple:
        """
        function validates if a string is valid to be stored in the database.
        Args:
            string (str): string to validate.
            max_length (int): max length of the string.
            empty (bool): True if the string could be empty.
        Returns:
            (invalid:bool, str:error message)
        """
        if not self.core:
            return False, "empty string is invalid"

        if isinstance(max_length, int):
            if len(self.core) > max_length:
                return False, f"Input string is too long, {max_length} characters max."

        return True, "string validated"


    def is_valid_email(self) -> tuple:
        """
        Validates if a string has a valid email format
        Args:
            email (str): email to validate
        Returns tuple:
            (valid:bool, str:error message)
                valid=True if the email is valid
                valid=False if the email is invalid
        """
        if len(self.core) > 320:
            return False, "invalid email length, max is 320 chars"

        # Regular expression that checks a valid email
        ereg = '^[\w]+[\._]?[\w]+[@]\w+[.]\w{2,3}$'
        # ereg = '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        if not re.search(ereg, self.core):
            return False, f"invalid email format"

        return True, "valid email format"


    def is_valid_pw(self) -> tuple:
        """
        Check if a password meets the minimum security parameters
        defined for this application.
        Args:
            password (str): password to validate.
        Returns tuple:
            (invalid:bool, str:error message)
        """
        # Regular expression that checks a secure password
        preg = '^.*(?=.{8,})(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).*$'

        if not re.search(preg, self.core):
            return False, "password is invalid"

        return True, "password validated"


    @staticmethod
    def random_password(length: int = 16) -> str:
        """
        function creates a random password, default length is 16 characters. pass in required length as an integer parameter
        """
        lower = string.ascii_lowercase
        upper = string.ascii_uppercase
        nums = string.digits
        symbols = string.punctuation

        all_cores = lower + upper + nums + symbols
        password = "".join(sample(all_cores, length))

        return password