from api.models.main import User
from api.extensions import db


class UserOperations:
    '''Object containing all the model queries to User model that can be made in 
    several parts of the application.
    '''
    def __init__(self, user_id:int=None, user_email:str=None) -> None:
        self.id = user_id
        self.email = user_email
        if user_id:
            self._user = db.session.query(User.id).get(user_id)
        elif user_email:
            self._user = db.session.query(User.id).filter(User.email == user_email).first()
        else:
            self._user = None

    @property
    def exists(self) -> bool:
        return True if self._user else False

    def query_user(self):
        '''query database using instance id variable'''
        return None if not self.id else \
            db.session.query(User).get(self.id)

    def query_user_by_email(self):
        '''get user matching instance email variable'''
        return None if not self.email else \
            db.session.query(User).filter(User.email == self.email).first()