import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-secret-key')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///campus.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
