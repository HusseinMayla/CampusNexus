from app.extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class User(UserMixin, db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(64), index=True, unique=True)
    email         = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(255))

    @property
    def verified_secondary_emails(self):
        return [e.email for e in self.secondary_emails if e.is_verified]

    def has_verified_domain(self, domain):
        if not domain:
            return True
        domain = domain.lower().strip()
        
        # Check primary email domain
        if self.email:
            parts = self.email.split('@')
            if len(parts) == 2 and parts[1].lower().strip() == domain:
                return True
                
        # Check secondary verified emails
        for sec_email in self.secondary_emails:
            if sec_email.is_verified:
                parts = sec_email.email.split('@')
                if len(parts) == 2 and parts[1].lower().strip() == domain:
                    return True
                    
        return False

    def __repr__(self):
        return f'<User {self.name}>'

class Campus(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(128), index=True, unique=True, nullable=False)
    description  = db.Column(db.Text)
    banner_image = db.Column(db.String(255))
    map_image    = db.Column(db.String(255))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id   = db.Column(db.Integer, db.ForeignKey('user.id'))
    center_lat   = db.Column(db.Float)
    center_lng   = db.Column(db.Float)
    domain       = db.Column(db.String(64), nullable=True)

    clubs   = db.relationship('Club',   backref='campus', lazy=True, cascade='all, delete-orphan')
    offices = db.relationship('Office', backref='campus', lazy=True, cascade='all, delete-orphan')
    members = db.relationship('CampusMember', backref='campus', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Campus {self.name}>'

class CampusMember(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campus_id  = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    role       = db.Column(db.String(20), default='user', nullable=False) # 'owner', 'admin', 'user'
    joined_at  = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'campus_id'),)

class Club(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    campus_id   = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    lat         = db.Column(db.Float)
    lng         = db.Column(db.Float)

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
    campus_id   = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    creator_id  = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date        = db.Column(db.DateTime, nullable=False)
    end_date    = db.Column(db.DateTime, nullable=False)
    lat         = db.Column(db.Float, nullable=False)
    lng         = db.Column(db.Float, nullable=False)

    campus      = db.relationship('Campus', backref=db.backref('events', lazy=True, cascade='all, delete-orphan'))
    creator     = db.relationship('User', backref=db.backref('created_events', lazy=True))

    def __repr__(self):
        return f'<Event {self.title}>'

class UserEmail(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email       = db.Column(db.String(120), unique=True, index=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('secondary_emails', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<UserEmail {self.email} (Verified: {self.is_verified})>'

class CampusReport(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    campus_id   = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reason      = db.Column(db.String(255), nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('reporter_id', 'campus_id'),)

    campus   = db.relationship('Campus', backref=db.backref('reports', lazy=True, cascade='all, delete-orphan'))
    reporter = db.relationship('User', backref=db.backref('reports_submitted', lazy=True))

    def __repr__(self):
        return f'<CampusReport reporter_id={self.reporter_id} campus_id={self.campus_id}>'

class Notification(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title       = db.Column(db.String(128), nullable=False)
    message     = db.Column(db.Text, nullable=False)
    is_read     = db.Column(db.Boolean, default=False, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    link        = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Notification {self.title} (Read: {self.is_read})>'

class Resource(db.Model):
    id                = db.Column(db.Integer, primary_key=True)
    title             = db.Column(db.String(128), nullable=False)
    description       = db.Column(db.Text)
    file_url          = db.Column(db.String(255))
    uploaded_at       = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    campus_id         = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    uploader_id       = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_code       = db.Column(db.String(32), nullable=True)
    file_type         = db.Column(db.String(16), nullable=True)
    original_filename = db.Column(db.String(255), nullable=True)

    uploader    = db.relationship('User', backref=db.backref('resources', lazy=True, cascade='all, delete-orphan'))
    campus      = db.relationship('Campus', backref=db.backref('resources', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Resource {self.title}>'

class MarketListing(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    price       = db.Column(db.Float, nullable=False)
    image_url   = db.Column(db.String(255))
    contact     = db.Column(db.String(128), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    campus_id   = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    seller_id   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    seller      = db.relationship('User', backref=db.backref('listings', lazy=True, cascade='all, delete-orphan'))
    campus      = db.relationship('Campus', backref=db.backref('listings', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<MarketListing {self.title}>'

class TutorPost(db.Model):
    __tablename__ = 'tutor_post'
    id         = db.Column(db.Integer, primary_key=True)
    campus_id  = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    poster_id  = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name  = db.Column(db.String(128), nullable=False)
    email      = db.Column(db.String(128), nullable=False)
    role       = db.Column(db.String(16), nullable=False)
    courses    = db.Column(db.String(512), nullable=False)
    method     = db.Column(db.String(32), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    poster = db.relationship('User', backref=db.backref('tutor_posts', lazy=True))
    campus = db.relationship('Campus', backref=db.backref('tutor_posts', lazy=True, cascade='all, delete-orphan'))

