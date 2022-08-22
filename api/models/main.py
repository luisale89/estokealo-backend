from api.extensions import db
from api.utils import helpers as h
from datetime import datetime, timedelta
from typing import Union
from werkzeug.security import generate_password_hash
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import backref
from sqlalchemy import func


class User(db.Model):
    __tablename__="user"
    id = db.Column(db.Integer, primary_key=True)
    _email = db.Column(db.String(256), unique=True, nullable=False)
    _email_confirmed = db.Column(db.Boolean, default=False)
    _password_hash = db.Column(db.String(256), nullable=False)
    _signup_completed = db.Column(db.Boolean, default=False)
    _signup_date = db.Column(db.DateTime, default=datetime.utcnow)
    _profile_image = db.Column(db.String(256), default="")
    first_name = db.Column(db.String(128), default="")
    last_name = db.Column(db.String(128), default="")
    phone = db.Column(db.String(64), default="")
    address = db.Column(JSON, default={"address": {}})

    def __repr__(self) -> str:
        return f"Users(email={self._email})"

    def serialize(self) -> dict:
        return {
            "ID": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "profile_image": self._profile_img
        }

    def serialize_all(self) -> dict:
        return {
            **self.serialize(),
            "signup_date": h.normalize_datetime(self._signup_date),
            "signup_completed": self._signup_completed,
            "phone": self.phone,
            "email": self._email,
            "email_confirmed": self._email_confirmed,
            "address": self.address.get("address", {})
        }

    @property
    def email(self):
        return self._email

    @property
    def password(self):
        raise AttributeError("Can't view user's password")

    @password.setter
    def password(self, password):
        self._password_hash = generate_password_hash(password, method='sha256')

    