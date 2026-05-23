from app.extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import secrets

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class User(UserMixin, db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(64), index=True, unique=True)
    email         = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(255))

    def __repr__(self):
        return f'<User {self.name}>'

class Campus(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(128), index=True, nullable=False)
    description  = db.Column(db.Text)
    banner_image = db.Column(db.String(255))
    map_image    = db.Column(db.String(255))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id   = db.Column(db.Integer, db.ForeignKey('user.id'))
    center_lat   = db.Column(db.Float)
    center_lng   = db.Column(db.Float)
    invite_code  = db.Column(db.String(10), unique=True, default=lambda: secrets.token_urlsafe(6))

    clubs   = db.relationship('Club',   backref='campus', lazy=True, cascade='all, delete-orphan')
    offices = db.relationship('Office', backref='campus', lazy=True, cascade='all, delete-orphan')
    members = db.relationship('CampusMember', backref='campus', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Campus {self.name}>'

class CampusMember(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campus_id  = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    joined_at  = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'campus_id'),)

class Club(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    campus_id   = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    lat         = db.Column(db.Float)
    lng         = db.Column(db.Float)
    events      = db.relationship('Event', backref='club', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Club {self.name}>'

class Office(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    campus_id   = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    lat         = db.Column(db.Float)
    lng         = db.Column(db.Float)

    def __repr__(self):
        return f'<Office {self.name}>'

class Event(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    club_id     = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    date        = db.Column(db.DateTime)
    lat         = db.Column(db.Float)
    lng         = db.Column(db.Float)

    def __repr__(self):
        return f'<Event {self.title}>'
