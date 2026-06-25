import os
from flask import Flask
from config import Config
from app.extensions import db, login_manager, mail



def create_app(config_class=Config):
    app = Flask(__name__)
    
    # Load general configurations (SECRET_KEY, MAIL settings, etc.) from config.py
    app.config.from_object(config_class)

    # configure database in Flask instance folder
    db_path = os.path.join(app.instance_path, 'campus.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    #check if folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions 
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Redirect users to the login page if they try to access a @login_required route while logged out
    login_manager.login_view = 'auth.page'
    
    # Import database models so SQLAlchemy registers them with metadata
    from app import models

    # Import Blueprints (modular route groups)
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.map.routes import map_bp
    from app.study.routes import study_bp

    # Register Blueprints with the Flask application
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(map_bp)
    app.register_blueprint(study_bp)

    # register app for the db since it is in a diff folder
    with app.app_context():
        db.create_all()  # create database

    return app
