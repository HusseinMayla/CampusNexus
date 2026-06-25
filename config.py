import os

class Config:
    # SECRET_KEY signs session cookies and tokens. In production, set this in the .env file.
    # The fallback string is fine for local dev but must never be used in a real deployment
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-secret-key')

    # Default database URI — overridden in __init__.py to point to the instance/ folder
    SQLALCHEMY_DATABASE_URI = 'sqlite:///campus.db'

    # Disable SQLAlchemy change tracking (saves memory; we don't use this feature)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Email (Flask-Mail) ────────────────────────────────────────────────────
    # Used only for sending verification and password-reset emails from the app's sender account.
    # Users' own email domains (e.g. .edu.lb) are unrelated — those are just login credentials.
    # MAIL_USERNAME and MAIL_PASSWORD are loaded from .env for security
    MAIL_SERVER   = 'smtp.gmail.com'
    MAIL_PORT     = 587
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')         # sender Gmail address
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')         # Gmail app password (not the account password)
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')   # "From:" field in outgoing emails
