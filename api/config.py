import os
import datetime


class Config(object):
    DEBUG = False
    DEVELOPMENT = False
    TESTING = False
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(days=1)
    SQLALCHEMY_DATABASE_URI = os.environ.get("MAIN_DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    pass


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    PROPAGATE_EXCEPTIONS = None


class TestingConfig(Config):
    TESTING = True
