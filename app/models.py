from app.extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime, timedelta

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(255))
    is_verified = db.Column(db.Boolean, default=False)

    def has_verified_domain(self, domain):
        if not domain:
            return True
        domain = domain.lower().strip()
        if self.email and self.email.split('@')[1].lower() == domain:
            return True
        for sec_email in self.secondary_emails:
            if sec_email.is_verified and sec_email.email.split('@')[1].lower() == domain:
                return True
        return False

    def is_campus_owner(self, campus_id):
        campus = Campus.query.get(campus_id)
        return campus is not None and campus.creator_id == self.id

    def __repr__(self):
        return f'<User {self.name}>'

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class Campus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, unique=True, nullable=False)
    description = db.Column(db.Text)
    banner_image = db.Column(db.String(255))
    map_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    center_lat = db.Column(db.Float)
    center_lng = db.Column(db.Float)
    domain = db.Column(db.String(64), nullable=True)

    clubs = db.relationship('Club', backref='campus', lazy=True, cascade='all, delete-orphan')
    offices = db.relationship('Office', backref='campus', lazy=True, cascade='all, delete-orphan')
    members = db.relationship('CampusMember', backref='campus', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Campus {self.name}>'

class CampusMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False) # 'owner', 'moderator', 'user'
    joined_at = db.Column(db.DateTime, default=datetime.now)
    __table_args__ = (db.UniqueConstraint('user_id', 'campus_id'),)

    user = db.relationship('User', backref=db.backref('campus_memberships', lazy=True, cascade='all, delete-orphan'))

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)

    def __repr__(self):
        return f'<Club {self.name}>'

class Office(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)

    def __repr__(self):
        return f'<Office {self.name}>'

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    campus = db.relationship('Campus', backref=db.backref('events', lazy=True, cascade='all, delete-orphan'))
    creator = db.relationship('User', backref=db.backref('created_events', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Event {self.title}>'

class UserEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('User', backref=db.backref('secondary_emails', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<UserEmail {self.email} (Verified: {self.is_verified})>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    link = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Notification {self.title} (Read: {self.is_read})>'

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    file_url = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_code = db.Column(db.String(32), nullable=True)
    chapters = db.Column(db.String(512), nullable=True)
    file_type = db.Column(db.String(16), nullable=True)
    original_filename = db.Column(db.String(255), nullable=True)

    uploader = db.relationship('User', backref=db.backref('resources', lazy=True, cascade='all, delete-orphan'))
    campus = db.relationship('Campus', backref=db.backref('resources', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Resource {self.title}>'

class TutorPost(db.Model):
    __tablename__ = 'tutor_post'
    id = db.Column(db.Integer, primary_key=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(16), nullable=False)
    courses = db.Column(db.String(512), nullable=False)
    method = db.Column(db.String(32), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    poster = db.relationship('User', backref=db.backref('tutor_posts', lazy=True, cascade='all, delete-orphan'))
    campus = db.relationship('Campus', backref=db.backref('tutor_posts', lazy=True, cascade='all, delete-orphan'))


class ResourceRequest(db.Model):
    __tablename__ = 'resource_request'
    id = db.Column(db.Integer, primary_key=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    course_code = db.Column(db.String(32), nullable=False)
    chapters = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    poster = db.relationship('User', backref=db.backref('resource_requests', lazy=True, cascade='all, delete-orphan'))
    campus = db.relationship('Campus', backref=db.backref('resource_requests', lazy=True, cascade='all, delete-orphan'))


class ChatRoom(db.Model):
    __tablename__ = 'chat_room'
    id = db.Column(db.Integer, primary_key=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    campus = db.relationship('Campus', backref=db.backref('chat_rooms', lazy=True, cascade='all, delete-orphan'))
    messages = db.relationship('ChatMessage', backref='room', lazy=True, cascade='all, delete-orphan')
    members = db.relationship('ChatMember', backref='room', lazy=True, cascade='all, delete-orphan')


class ChatMember(db.Model):
    __tablename__ = 'chat_member'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)
    last_read_at = db.Column(db.DateTime, nullable=True)
    joined_at = db.Column(db.DateTime, default=datetime.now)
    __table_args__ = (db.UniqueConstraint('user_id', 'room_id'),)

    user = db.relationship('User', backref=db.backref('chat_memberships', lazy=True, cascade='all, delete-orphan'))


class ChatMessage(db.Model):
    __tablename__ = 'chat_message'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.now)

    sender = db.relationship('User', backref=db.backref('chat_messages', lazy=True, cascade='all, delete-orphan'))


class StudyRoom(db.Model):
    __tablename__ = 'study_room'
    id = db.Column(db.Integer, primary_key=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    location = db.Column(db.String(128), nullable=False)
    session_time = db.Column(db.DateTime, nullable=False)
    max_members = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    campus = db.relationship('Campus', backref=db.backref('study_rooms', lazy=True, cascade='all, delete-orphan'))
    owner = db.relationship('User', backref=db.backref('owned_study_rooms', lazy=True, cascade='all, delete-orphan'))
    members = db.relationship('StudyRoomMember', backref='room', lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('StudyRoomMessage', backref='room', lazy=True, cascade='all, delete-orphan')

    def is_expired(self):
        return datetime.now() > self.session_time + timedelta(hours=2)

    def member_count(self):
        return len(self.members)


class StudyRoomMember(db.Model):
    __tablename__ = 'study_room_member'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('study_room.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    last_read_at = db.Column(db.DateTime, nullable=True)
    joined_at = db.Column(db.DateTime, default=datetime.now)
    __table_args__ = (db.UniqueConstraint('room_id', 'user_id'),)

    user = db.relationship('User', backref=db.backref('study_room_memberships', lazy=True, cascade='all, delete-orphan'))


class StudyRoomMessage(db.Model):
    __tablename__ = 'study_room_message'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('study_room.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.now)

    sender = db.relationship('User', backref=db.backref('study_room_messages', lazy=True, cascade='all, delete-orphan'))


class EventParticipation(db.Model):
    __tablename__ = 'event_participation'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_interested = db.Column(db.Boolean, default=False, nullable=False)
    want_notification = db.Column(db.Boolean, default=False, nullable=False)
    notification_sent = db.Column(db.Boolean, default=False, nullable=False)

    __table_args__ = (db.UniqueConstraint('user_id', 'event_id'),)

    event = db.relationship('Event', backref=db.backref('participations', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('event_participations', lazy=True, cascade='all, delete-orphan'))


class EventCreationLog(db.Model):
    __tablename__ = 'event_creation_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    user = db.relationship('User', backref=db.backref('event_creation_logs', lazy=True, cascade='all, delete-orphan'))
