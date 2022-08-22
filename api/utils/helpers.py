from typing import Union
from datetime import datetime, timedelta, timezone
import os, re, string
from dateutil.parser import parse, ParserError
from itsdangerous import BadSignature, Signer


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
        unsigned_value = signer.unsign(qrcode).decode("utf-8")
        return unsigned_value[len(QR_PREFIX):]

    except BadSignature:
        return None