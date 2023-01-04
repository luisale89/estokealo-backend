from api.extensions import db
from api.utils import helpers as h
from datetime import datetime
from werkzeug.security import generate_password_hash
from sqlalchemy.dialects.postgresql import JSON
from typing import Union

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
            "id": self.id,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self._email,
            "signupCompleted": self._signup_completed
        }
    
    def serialize(self) -> dict:
        return self._base_serializer()

    def serialize_all(self) -> dict:
        base_dict = self._base_serializer()
        base_dict.update({
            "signupDate": h.datetime_formatter(self._signup_date),
            "phone": self.phone,
            "profileImage": self._profile_image,
            "address": self.address.get("address", {})
        })
        return base_dict

    def serialize_public_info(self) -> dict:
        base_dict = self._base_serializer()
        base_dict.update({
            "companies": list(map(lambda x: x.company.serialize(),
                filter(lambda x: x.is_enabled, self.roles.all()))),
        })
        return base_dict

    @classmethod
    def filter_user(cls, email:str = "", user_id:int = 0) -> Union[object, None]:
        """
        Filter a user instance by its email address or id
        """
        user = db.session.query(cls)
        if user_id:
            return user.get(id)

        return user.filter(User._email == email).first()

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
        return self._password_hash

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
    _inv_status = db.Column(db.String(12), default="pending") #["pending", "accepted", "rejected"]
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
            "id": self.id,
            "relationDate": h.datetime_formatter(self._relation_date),
            "isActive": self._is_active,
            "invitationStatus": self._inv_status,
            "roleFunction": self.role_function.serialize()
        }

    def serialize(self) -> dict:
        return self._base_serializer()
    
    def serialize_with_user(self) -> dict:
        base_dict = self._base_serializer()
        base_dict.update({
            "company": self.company.serialize()
        })
        return base_dict

    def serialize_with_company(self) -> dict:
        base_dict = self._base_serializer()
        base_dict.update({
            "user": self.user.serialize()
        })
        return base_dict


    @property
    def is_active(self) -> bool:
        return self._is_active

    @is_active.setter
    def is_active(self, new_val:bool) -> None:
        self._is_active = new_val

    @property
    def is_enabled(self) -> bool:
        return True if self._inv_status == "accepted" and self._is_active else False

    @property
    def inv_status(self):
        return self._inv_status

    @inv_status.setter
    def inv_status(self, new_value:str):
        self._inv_status = new_value


class Company(db.Model):

    BASE_CURRENCY= {"name": "Dólar Estadounidense", "iso": "USD", "symbol": "$"}

    __tablename__= "company"
    id = db.Column(db.Integer, primary_key=True)
    _created_at = db.Column(db.DateTime, default=datetime.utcnow)
    _logo = db.Column(db.String(256), default="")
    name = db.Column(db.String(64), nullable=False)
    timezone_name = db.Column(db.String(64), default="america/caracas")
    address = db.Column(JSON, default={"address": {}})
    currency_data = db.Column(JSON, default={"currency_data": BASE_CURRENCY})
    currency_rate = db.Column(db.Float(), default=1.0)
    #relationships
    roles = db.relationship("Role", back_populates="company", lazy="dynamic")

    def __repr__(self) -> str:
        return f"Company(id={self.id})"

    def _base_serializer(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "logo": self._logo
        }

    def serialize(self):
        return self._base_serializer()

    def serialize_all(self):
        base_dict = self._base_serializer()
        base_dict.update({
            "timezoneName": self.timezone_name,
            "address": self.address.get("address", {}),
            "currency": {
                **self.currency_data.get("currency_data", self.BASE_CURRENCY),
                "rate": self.currency_rate
            },
            "creationDate": h.datetime_formatter(self._created_at)
        })
        return base_dict

    def dolarize(self, value:float) -> float:
        """ Convert 'price' parameter to the equivalent of the base currency"""
        if self.currency_rate:
            return round(value / self.currency_rate, 2)

        return 0.0


class Store(db.Model):
    __tablename__ = "store"
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(256), nullable=False)

    def __repr__(self) -> str:
        return f"Store(id={self.id})"

    def _base_serialize(self) -> dict:
        return {
            "record_id": self.id,
            "name": self.name
        }