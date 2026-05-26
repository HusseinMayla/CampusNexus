import os
from flask import Flask
from config import Config
from app.extensions import db, login_manager

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Use SQLite or PostgreSQL based on environments.
    if os.environ.get('DATABASE_URL'):
        database_url = os.environ.get('DATABASE_URL')
        # SQLAlchemy requires 'postgresql://' instead of 'postgres://'
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    elif os.environ.get('VERCEL'):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/campus.db'
    else:
        # For local development, use the database in the instance folder
        db_path = os.path.join(app.instance_path, 'campus.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    # Ensure the instance folder exists for local development
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.page'

    # Import models to register user_loader
    from app import models

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.events.routes import events_bp
    from app.map.routes import map_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(map_bp)

    @app.context_processor
    def inject_chat_sidebar():
        from flask_login import current_user
        from flask import request as req
        if not current_user.is_authenticated:
            return {'sidebar_chat': []}
        if req.is_json or req.path.endswith(('/send', '/poll', '/join', '/leave')):
            return {'sidebar_chat': []}
        from app.models import CampusMember, ChatMember, ChatMessage
        # Seed every campus the user belongs to (even those with no rooms yet)
        by_campus = {}
        for m in CampusMember.query.filter_by(user_id=current_user.id).all():
            c = m.campus
            by_campus[c.id] = {'campus_id': c.id, 'campus_name': c.name, 'rooms': []}
        # Overlay joined chat rooms with unread status
        for cm in ChatMember.query.filter_by(user_id=current_user.id).all():
            room = cm.room
            cid  = room.campus_id
            if cid not in by_campus:
                by_campus[cid] = {'campus_id': cid, 'campus_name': room.campus.name, 'rooms': []}
            last_msg = ChatMessage.query.filter_by(room_id=room.id).order_by(ChatMessage.sent_at.desc()).first()
            has_unread = bool(last_msg and (cm.last_read_at is None or last_msg.sent_at > cm.last_read_at))
            by_campus[cid]['rooms'].append({'id': room.id, 'name': room.name, 'has_unread': has_unread})
        return {'sidebar_chat': list(by_campus.values())}

    @app.errorhandler(500)
    def internal_error(error):
        import traceback
        app.logger.error(traceback.format_exc())
        return "<h1>Something went wrong.</h1><p>Please try again later.</p>", 500

    # Create the database tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.error(f"Database creation failed: {e}")

    return app
