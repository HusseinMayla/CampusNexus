from flask import Flask
from config import Config
from app.extensions import db, login_manager

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Use SQLite. If on Vercel, we must use /tmp because the root is read-only.
    if os.environ.get('VERCEL'):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/campus.db'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus.db'

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Import models to register user_loader
    from app import models

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.events.routes import events_bp
    from app.notes.routes import notes_bp
    from app.chat.routes import chat_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(chat_bp)

    return app
