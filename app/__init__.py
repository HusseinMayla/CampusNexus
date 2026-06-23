import os
from datetime import datetime, timedelta
from flask import Flask, request
from flask_login import current_user
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
    from app.study import study_bp

    # Register Blueprints with the Flask application
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(map_bp)
    app.register_blueprint(study_bp)

    # --- GLOBAL CONTEXT PROCESSOR ---
    # This function fetches data for: study rooms, chat rooms, notifications which are route independent.
    def inject_global_data():
        # List of endpoints/paths to skip sidebar queries on (performance optimization for AJAX requests)
        skip_paths = ('/send', '/poll', '/join', '/leave', '/create', '/delete', '/add', '/courses/remove')

        # If user is not logged in, return empty sidebar variables
        if not current_user.is_authenticated:
            return {'sidebar_chat': [], 'sidebar_study': [], 'unread_notifications_count': 0}

        # If it's a JSON response or an excluded path, return empty variables to save database queries
        if request.is_json or request.path.endswith(skip_paths):
            return {'sidebar_chat': [], 'sidebar_study': [], 'unread_notifications_count': 0}

        from app.models import (CampusMember, ChatMember, ChatMessage,
                                StudyRoomMember, StudyRoomMessage, StudyRoom, Notification)
        # -- Ingest Chat Sidebar data --
        by_campus = {}
        # Fetch campuses that the current logged-in user belongs to
        for m in CampusMember.query.filter_by(user_id=current_user.id).all():
            c = m.campus
            by_campus[c.id] = {'campus_id': c.id, 'campus_name': c.name, 'rooms': []}
            
        # Fetch active chat rooms the user has joined and check if they have unread messages
        for cm in ChatMember.query.filter_by(user_id=current_user.id).all():
            room = cm.room
            cid = room.campus_id
            if cid not in by_campus:
                by_campus[cid] = {'campus_id': cid, 'campus_name': room.campus.name, 'rooms': []}
            last_msg = ChatMessage.query.filter_by(room_id=room.id)\
                                        .order_by(ChatMessage.sent_at.desc()).first()
            has_unread = last_msg and (cm.last_read_at is None or last_msg.sent_at > cm.last_read_at)
            by_campus[cid]['rooms'].append({'id': room.id, 'name': room.name,
                                            'has_unread': has_unread})

        # -- Ingest Study Room Sidebar data --
        # Hide study rooms whose sessions occurred more than 2 hours ago
        cutoff = datetime.now() - timedelta(hours=2)
        study_items = []
        for srm in StudyRoomMember.query.filter_by(user_id=current_user.id).all():
            room = srm.room
            if room.session_time < cutoff:
                continue
            last_msg = StudyRoomMessage.query.filter_by(room_id=room.id)\
                                             .order_by(StudyRoomMessage.sent_at.desc()).first()
            has_unread = last_msg and (srm.last_read_at is None or last_msg.sent_at > srm.last_read_at)
            study_items.append({
                'room_id': room.id,
                'campus_id': room.campus_id,
                'campus_name': room.campus.name,
                'title': room.title,
                'session_time': room.session_time,
                'location': room.location,
                'member_count': room.member_count(),
                'max_members': room.max_members,
                'has_unread': has_unread,
            })
        study_items.sort(key=lambda item: item['session_time'])

        # -- Unread Notification Badge Count --
        unread_notifications_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

        return {
            'sidebar_chat': list(by_campus.values()),
            'sidebar_study': study_items,
            'unread_notifications_count': unread_notifications_count
        }


    # register app for the db since it is in a diff folder
    with app.app_context():
        db.create_all()  # create database

    return app
