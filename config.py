import os

class Config:
    SECRET_KEY = 'secret-key-for-now'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///campus.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
