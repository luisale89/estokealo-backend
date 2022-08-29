from redislite import Redis
import os, datetime
from api.utils import helpers as h

class RedisClient:

    # REDIS_DB_PATH = os.environ.get("REDIS_DB_PATH", os.path.join("/tmp/estokealo.db")
    REDIS_DB_PATH = os.path.join("/tmp/estokealo.db")
    
    def __init__(self) -> None:
        pass

    def set_connection(self):
        return Redis(self.REDIS_DB_PATH)

    def add_jwt_to_blocklist(self, claims) -> tuple:
        '''
        function to save a jwt in redis
        * returns tuple -> (success:bool, msg:str)
        '''
        rdb = self.set_connection()
        jti = claims["jti"]
        jwt_exp = h.epoch_utc_to_datetime(claims["exp"])
        now_date = datetime.datetime.utcnow()

        if jwt_exp < now_date:
            return True, "jwt is already expired"

        expires = jwt_exp - now_date
        rdb.set(jti, "", ex=expires)
        return True, "jwt in blocklist"