from flask_sqlalchemy import SQLAlchemy  # ORM — maps Python classes to database tables
from flask_login import LoginManager     # handles login sessions, current_user, @login_required
from flask_mail import Mail              # sends emails (verification links, password reset)

# These objects are created without a Flask app so they can be shared across the package.
# They're attached to an actual app later via init_app() in app/__init__.py
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # redirect here when @login_required fails (overridden in __init__.py)
mail = Mail()
