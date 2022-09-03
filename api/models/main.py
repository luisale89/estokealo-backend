from api.extensions import db
from api.utils import helpers as h
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import backref
from sqlalchemy import func

#models
from .global_models import *

class User(db.Model):
    __tablename__="user"
    id = db.Column(db.Integer, primary_key=True)
    _email = db.Column(db.String(256), unique=True, nullable=False)
    _password_hash = db.Column(db.String(256), nullable=False)
    _signup_completed = db.Column(db.Boolean, default=False)
    _signup_date = db.Column(db.DateTime, default=datetime.utcnow)
    _profile_image = db.Column(db.String(256), default="")
    first_name = db.Column(db.String(128), default="")
    last_name = db.Column(db.String(128), default="")
    phone = db.Column(db.String(64), default="")
    address = db.Column(JSON, default={"address": {}})
    #relationships
    roles = db.relationship("Role", back_populates="user", lazy="dynamic")

    def __repr__(self) -> str:
        return f"User(id={self.id})"

    def _base_serializer(self) -> dict:
        return {
            "ID": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "signup_completed": self._signup_completed
        }
    
    def serialize(self) -> dict:
        return {
            self.__tablename__: self._base_serializer()
        }

    def serialize_all(self) -> dict:
        return {
            self.__tablename__: self._base_serializer() | {
                "signup_date": h.datetime_formatter(self._signup_date),
                "phone": self.phone,
                "email": self._email,
                "profile_image": self._profile_image,
                "address": self.address.get("address", {})
            }
        }

    @property
    def is_enabled(self) -> bool:
        return self.signup_completed

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, new_email):
        self._email = new_email

    @property
    def password(self):
        raise AttributeError("Can't view user's password")

    @password.setter
    def password(self, password):
        self._password_hash = generate_password_hash(password, method='sha256')

    @property
    def signup_completed(self):
        return self._signup_completed

    @signup_completed.setter
    def signup_completed(self, new_state:bool):
        self._signup_completed = new_state


class Role(db.Model):
    __tablename__="role"
    id = db.Column(db.Integer, primary_key=True)
    _relation_date = db.Column(db.DateTime, default=datetime.utcnow)
    _inv_accepted = db.Column(db.Boolean, default=False)
    _is_active = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    role_function_id = db.Column(db.Integer, db.ForeignKey("role_function.id"), nullable=False)
    #relationships
    user = db.relationship("User", back_populates="roles", lazy="joined")
    company = db.relationship("Company", back_populates="roles", lazy="joined")
    role_function = db.relationship("RoleFunction", back_populates="roles", lazy="joined")

    def __repr__(self) -> str:
        return f"Role(id={self.id})"

    def _base_serializer(self) -> dict:
        return {
            "ID": self.id,
            "relation_date": h.normalize_datetime(self._relation_date),
            "is_active": self._is_active,
            "is_invitation_accepted": self._inv_accepted
        }

    def serialize(self) -> dict:
        return {
            self.__tablename__: self._base_serializer()
        }

    def serialize_all(self) -> dict:
        return {
            self.__tablename__: self._base_serializer() | {
                **self.user.serialize(),
                **self.company.serialize(),
                **self.role_function.serialize()
            }
        }

    @property
    def is_enabled(self) -> bool:
        return True if self._inv_accepted and self._is_active else False


class Company(db.Model):

    BASE_CURRENCY= {"name": "Dólar Estadounidense", "ISO": "USD", "Symbol": "$"}

    __tablename__= "company"
    id = db.Column(db.Integer, primary_key=True)
    _created_at = db.Column(db.DateTime, default=datetime.utcnow)
    _logo = db.Column(db.String(256), default="")
    name = db.Column(db.String(64), nullable=False)
    timezone_name = db.Column(db.String(64), default="america/caracas")
    address = db.Column(JSON, default={"address": {}})
    currency_data = db.Column(JSON, default={"currency": BASE_CURRENCY})
    currency_rate = db.Column(db.Float(), default=1.0)
    #relationships
    roles = db.relationship("Role", back_populates="company", lazy="dynamic")

    def __repr__(self) -> str:
        return f"Company(id={self.id})"

    def _base_serializer(self) -> dict:
        return {
            "ID": self.id,
            "name": self.name,
            "logo": self._logo
        }

    def serialize(self):
        return {
            self.__tablename__: self._base_serializer()
        }

    def serialize_all(self):
        return {
            self.__tablename__: self._base_serializer() | {
                "timezone_name": self.timezone_name,
                "address": self.address.get("address", {}),
                "currency": {
                    **self.currency_data.get("currency", {}),
                    "rate": self.currency_rate,
                    "base": self.BASE_CURRENCY
                },
                "creation_date": h.normalize_datetime(self._created_at)
            }
        }

    def dolarize(self, value:float) -> float:
        ''' Convert 'price' parameter to the equivalent of the base currency'''
        if self.currency_rate:
            return round(value / self.currency_rate, 2)

        return 0.0