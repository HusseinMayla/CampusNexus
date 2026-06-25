from app.extensions import db, login_manager   # db = SQLAlchemy instance, login_manager = Flask-Login instance
from flask_login import UserMixin               # UserMixin gives is_authenticated, is_active, get_id() for free
from datetime import datetime, timedelta        # datetime for default timestamps, timedelta for is_expired() check


# ── User ──────────────────────────────────────────────────────────────────────

# The central user account. UserMixin makes Flask-Login work (is_authenticated, get_id, etc.)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True, unique=True)  # primary university email
    password_hash = db.Column(db.String(255))                   # bcrypt hash, never plain text
    is_verified = db.Column(db.Boolean, default=False)          # must verify email before logging in

    # Returns True if the user has a verified email matching the campus domain.
    # Checks both primary email and any verified secondary emails
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


# Tells Flask-Login how to reload a user from their ID stored in the session cookie
@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))


# ── Campus ────────────────────────────────────────────────────────────────────

# A virtual campus that users can create and join. Owns clubs, offices, events, resources, etc.
class Campus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, unique=True, nullable=False)
    description = db.Column(db.Text)
    banner_image = db.Column(db.String(255))    # UUID-prefixed filename in /static/uploads/
    map_image = db.Column(db.String(255))        # blueprint image shown on the map page
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    center_y = db.Column(db.Float)              # optional default map view center (y%)
    center_x = db.Column(db.Float)              # optional default map view center (x%)
    domain = db.Column(db.String(64), nullable=True)    # university email domain restriction (e.g. "aub.edu.lb")

    # Cascade: deleting a campus deletes its clubs, offices, and member records
    clubs = db.relationship('Club', backref='campus', lazy=True, cascade='all, delete-orphan')
    offices = db.relationship('Office', backref='campus', lazy=True, cascade='all, delete-orphan')
    members = db.relationship('CampusMember', backref='campus', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Campus {self.name}>'


# ── CampusMember ──────────────────────────────────────────────────────────────

# Join table between User and Campus. role can be 'user', 'moderator', or 'owner'
class CampusMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'owner', 'moderator', 'user'
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Unique constraint removed for student simplicity; checks are done in python code

    # cascade='all, delete-orphan' on the backref means deleting a User removes their memberships
    user = db.relationship('User', backref=db.backref('campus_memberships', lazy=True, cascade='all, delete-orphan'))


# ── Map Pins: Club, Office, Event ─────────────────────────────────────────────

# A campus club shown as a pin on the map. x/y are percentage positions on the blueprint image
class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    y = db.Column(db.Float)     # vertical position on blueprint image (0-100%)
    x = db.Column(db.Float)     # horizontal position on blueprint image (0-100%)

    def __repr__(self):
        return f'<Club {self.name}>'


# An office or administrative location shown as a pin on the map
class Office(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    y = db.Column(db.Float)
    x = db.Column(db.Float)

    def __repr__(self):
        return f'<Office {self.name}>'


# A time-bounded event shown as a pin on the map. date = start time, end_date = end time (both UTC)
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)           # UTC start time
    end_date = db.Column(db.DateTime, nullable=False)       # UTC end time (computed from duration in JS)
    y = db.Column(db.Float, nullable=False)
    x = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Cascade: deleting a campus deletes its events; deleting a user deletes events they created
    campus = db.relationship('Campus', backref=db.backref('events', lazy=True, cascade='all, delete-orphan'))
    creator = db.relationship('User', backref=db.backref('created_events', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Event {self.title}>'


# ── Secondary Emails ──────────────────────────────────────────────────────────

# A user can add secondary university email addresses (e.g. to join campuses with different domains)
class UserEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)  # must click verification link before this email counts
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('secondary_emails', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<UserEmail {self.email} (Verified: {self.is_verified})>'


# ── Notifications ─────────────────────────────────────────────────────────────

# In-app notification delivered to a user (e.g. "Someone joined your study room").
# link is optional — allows clicking the notification to navigate to the relevant page
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    link = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Notification {self.title} (Read: {self.is_read})>'


# ── Resources ─────────────────────────────────────────────────────────────────

# A shared file (PDF, notes, etc.) uploaded to a campus.
# uploader_id is nullable — set to NULL when the uploader deletes their account so the file survives
class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    file_url = db.Column(db.String(255))        # path under /static/uploads/ (UUID-prefixed filename)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # nullable: survives account deletion
    course_code = db.Column(db.String(32), nullable=True)
    chapters = db.Column(db.String(512), nullable=True)     # comma-separated chapter list
    file_type = db.Column(db.String(16), nullable=True)     # e.g. 'pdf', 'docx'
    original_filename = db.Column(db.String(255), nullable=True)    # original name before UUID prefix

    # No cascade on uploader relationship — so resource stays when user is deleted (uploader_id → NULL)
    uploader = db.relationship('User', backref=db.backref('resources', lazy=True))
    campus = db.relationship('Campus', backref=db.backref('resources', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Resource {self.title}>'


# ── Tutor Market ──────────────────────────────────────────────────────────────

# A listing posted by a student offering tutoring or looking for a tutor
class TutorPost(db.Model):
    __tablename__ = 'tutor_post'
    id = db.Column(db.Integer, primary_key=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False)       # contact email (can differ from account email)
    role = db.Column(db.String(16), nullable=False)         # 'tutor' or 'student'
    courses = db.Column(db.String(512), nullable=False)     # comma-separated course list
    method = db.Column(db.String(32), nullable=False)       # 'online', 'in-person', 'hybrid', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    poster = db.relationship('User', backref=db.backref('tutor_posts', lazy=True, cascade='all, delete-orphan'))
    campus = db.relationship('Campus', backref=db.backref('tutor_posts', lazy=True, cascade='all, delete-orphan'))


# A request posted by a student looking for specific study materials
class ResourceRequest(db.Model):
    __tablename__ = 'resource_request'
    id = db.Column(db.Integer, primary_key=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    course_code = db.Column(db.String(32), nullable=False)
    chapters = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    poster = db.relationship('User', backref=db.backref('resource_requests', lazy=True, cascade='all, delete-orphan'))
    campus = db.relationship('Campus', backref=db.backref('resource_requests', lazy=True, cascade='all, delete-orphan'))


# ── Chat Rooms ────────────────────────────────────────────────────────────────

# A named chat channel inside a campus (up to 14 members, enforced in routes)
class ChatRoom(db.Model):
    __tablename__ = 'chat_room'
    id = db.Column(db.Integer, primary_key=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    campus = db.relationship('Campus', backref=db.backref('chat_rooms', lazy=True, cascade='all, delete-orphan'))
    messages = db.relationship('ChatMessage', backref='room', lazy=True, cascade='all, delete-orphan')
    members = db.relationship('ChatMember', backref='room', lazy=True, cascade='all, delete-orphan')


# Membership record linking a User to a ChatRoom.
# last_read_at tracks when the user last read the room (used to count unread messages)
class ChatMember(db.Model):
    __tablename__ = 'chat_member'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)
    last_read_at = db.Column(db.DateTime, nullable=True)    # NULL means never read (all messages are "unread")
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Unique constraint removed for student simplicity; checks are done in python code

    user = db.relationship('User', backref=db.backref('chat_memberships', lazy=True, cascade='all, delete-orphan'))


# A single message in a chat room
class ChatMessage(db.Model):
    __tablename__ = 'chat_message'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', backref=db.backref('chat_messages', lazy=True, cascade='all, delete-orphan'))


# ── Study Rooms ───────────────────────────────────────────────────────────────

# A temporary study session. Expires 2 hours after session_time and gets cleaned up on next browse load
class StudyRoom(db.Model):
    __tablename__ = 'study_room'
    id = db.Column(db.Integer, primary_key=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    location = db.Column(db.String(128), nullable=False)    # physical location description (e.g. "Library Room 3")
    session_time = db.Column(db.DateTime, nullable=False)   # UTC start time
    max_members = db.Column(db.Integer, nullable=False)     # 2-20, enforced in routes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    campus = db.relationship('Campus', backref=db.backref('study_rooms', lazy=True, cascade='all, delete-orphan'))
    owner = db.relationship('User', backref=db.backref('owned_study_rooms', lazy=True, cascade='all, delete-orphan'))
    members = db.relationship('StudyRoomMember', backref='room', lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('StudyRoomMessage', backref='room', lazy=True, cascade='all, delete-orphan')

    # Returns True if the session ended more than 2 hours ago
    def is_expired(self):
        return datetime.utcnow() > self.session_time + timedelta(hours=2)

    def member_count(self):
        return len(self.members)


# Membership record for a study room. last_read_at tracks unread messages in the room chat
class StudyRoomMember(db.Model):
    __tablename__ = 'study_room_member'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('study_room.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    last_read_at = db.Column(db.DateTime, nullable=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Unique constraint removed for student simplicity; checks are done in python code

    user = db.relationship('User', backref=db.backref('study_room_memberships', lazy=True, cascade='all, delete-orphan'))


# A single message in a study room chat
class StudyRoomMessage(db.Model):
    __tablename__ = 'study_room_message'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('study_room.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', backref=db.backref('study_room_messages', lazy=True, cascade='all, delete-orphan'))


# ── Event Participation ───────────────────────────────────────────────────────

# Tracks a user's interest in and notification preference for a map event
class EventParticipation(db.Model):
    __tablename__ = 'event_participation'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_interested = db.Column(db.Boolean, default=False, nullable=False)        # clicked "Interested"
    want_notification = db.Column(db.Boolean, default=False, nullable=False)    # wants an alert when event starts
    notification_sent = db.Column(db.Boolean, default=False, nullable=False)    # prevents duplicate start alerts

    # Unique constraint removed for student simplicity; checks are done in python code

    event = db.relationship('Event', backref=db.backref('participations', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('event_participations', lazy=True, cascade='all, delete-orphan'))


# Logs each time a student creates an event, used to enforce the 4-day cooldown between event creations
class EventCreationLog(db.Model):
    __tablename__ = 'event_creation_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('event_creation_logs', lazy=True, cascade='all, delete-orphan'))
