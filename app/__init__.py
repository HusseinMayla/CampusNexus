import os
import sys
from flask import Flask
from config import Config
from app.extensions import db, login_manager, socketio

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Use SQLite or PostgreSQL based on environments.
    # In local development, we default to SQLite even if a global DATABASE_URL is set (from another project).
    # We only use DATABASE_URL if we are deployed (Vercel/Railway) or if USE_POSTGRES is explicitly set.
    is_deployed = os.environ.get('VERCEL') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PORT')
    
    if os.environ.get('DATABASE_URL') and (is_deployed or os.environ.get('USE_POSTGRES')):
        database_url = os.environ.get('DATABASE_URL')
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        db_path = os.path.join(app.instance_path, 'campus.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'


    # Ensure the instance folder exists for local development
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.page'
    _async_mode = 'gevent' if 'gunicorn' in sys.argv[0] else 'threading'
    socketio.init_app(app, cors_allowed_origins='*', async_mode=_async_mode)

    from app import models

    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.events.routes import events_bp
    from app.map.routes import map_bp
    from app.study import study_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(map_bp)
    app.register_blueprint(study_bp)

    from app.study import events as _study_events  # registers socketio handlers  # noqa

    @app.context_processor
    def inject_global_data():
        from flask_login import current_user
        from flask import request as req
        from datetime import timedelta

        skip_paths = ('/send', '/poll', '/join', '/leave', '/create', '/delete', '/add', '/courses/remove')
        if not current_user.is_authenticated:
            return {'sidebar_chat': [], 'sidebar_study': [], 'unread_notifications_count': 0}
        if req.is_json or req.path.endswith(skip_paths):
            return {'sidebar_chat': [], 'sidebar_study': [], 'unread_notifications_count': 0}

        from app.models import (CampusMember, ChatMember, ChatMessage,
                                StudyRoomMember, StudyRoomMessage, StudyRoom, Notification)
        import datetime as dt

        # ── Chat sidebar ─────────────────────────────────────────
        by_campus = {}
        for m in CampusMember.query.filter_by(user_id=current_user.id).all():
            c = m.campus
            by_campus[c.id] = {'campus_id': c.id, 'campus_name': c.name, 'rooms': []}
        for cm in ChatMember.query.filter_by(user_id=current_user.id).all():
            room = cm.room
            cid  = room.campus_id
            if cid not in by_campus:
                by_campus[cid] = {'campus_id': cid, 'campus_name': room.campus.name, 'rooms': []}
            last_msg = ChatMessage.query.filter_by(room_id=room.id)\
                                        .order_by(ChatMessage.sent_at.desc()).first()
            has_unread = bool(last_msg and (cm.last_read_at is None
                                            or last_msg.sent_at > cm.last_read_at))
            by_campus[cid]['rooms'].append({'id': room.id, 'name': room.name,
                                            'has_unread': has_unread})

        # ── Study room sidebar ───────────────────────────────────
        cutoff = dt.datetime.utcnow() - timedelta(hours=2)
        study_items = []
        for srm in StudyRoomMember.query.filter_by(user_id=current_user.id).all():
            room = srm.room
            if room.session_time < cutoff:
                continue
            last_msg = StudyRoomMessage.query.filter_by(room_id=room.id)\
                                             .order_by(StudyRoomMessage.sent_at.desc()).first()
            has_unread = bool(last_msg and (srm.last_read_at is None
                                            or last_msg.sent_at > srm.last_read_at))
            study_items.append({
                'room_id':      room.id,
                'campus_id':    room.campus_id,
                'campus_name':  room.campus.name,
                'course_code':  room.course_code,
                'session_time': room.session_time,
                'chapter':      room.chapter,
                'location':     room.location,
                'member_count': room.member_count,
                'max_members':  room.max_members,
                'has_unread':   has_unread,
            })
        study_items.sort(key=lambda x: x['session_time'])

        # ── Unread notifications count ───────────────────────────
        unread_notifications_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

        return {
            'sidebar_chat': list(by_campus.values()),
            'sidebar_study': study_items,
            'unread_notifications_count': unread_notifications_count
        }

    @app.errorhandler(500)
    def internal_error(error):
        import traceback
        app.logger.error(traceback.format_exc())
        return "<h1>Something went wrong.</h1><p>Please try again later.</p>", 500

    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.error(f"Database creation failed: {e}")

    return app
