import os
import sys
from datetime import datetime, timedelta
import bcrypt

# Ensure the root directory is in sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from app.models import User, Campus, CampusMember, Club, Office, Event, ChatRoom, ChatMessage, ChatMember

def seed_db():
    app = create_app()
    with app.app_context():
        print("Ensuring database tables exist...")
        db.create_all()

        # Check if there is already data
        if Campus.query.first():
            print("Database already contains data. Skipping seeding to prevent duplication.")
            return

        print("Seeding mock data...")

        # 1. Create mock users
        password_hash1 = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        password_hash2 = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        password_hash3 = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        alice = User(name='Alice Smith', email='alice@university.edu', password_hash=password_hash1)
        bob = User(name='Bob Jones', email='bob@university.edu', password_hash=password_hash2)
        charlie = User(name='Charlie Brown', email='charlie@university.edu', password_hash=password_hash3)

        db.session.add_all([alice, bob, charlie])
        db.session.commit()
        print(f"Created users: {alice.name}, {bob.name}, {charlie.name}")

        # 2. Create a mock campus
        campus = Campus(
            name='Nexus University',
            description='The premier modern smart campus featuring advanced learning facilities and a vibrant student community.',
            banner_image='https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&w=1200&q=80',
            map_image='./app\static\images\default_blueprint.png',
            creator_id=alice.id,
            center_lat=42.3601,
            center_lng=-71.0942,
            domain='university.edu'
        )
        db.session.add(campus)
        db.session.commit()
        print(f"Created campus: {campus.name}")

        # 3. Add members to the campus
        m1 = CampusMember(user_id=alice.id, campus_id=campus.id, role='owner')
        m2 = CampusMember(user_id=bob.id, campus_id=campus.id, role='user')
        m3 = CampusMember(user_id=charlie.id, campus_id=campus.id, role='user')
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        # 4. Add Clubs & Offices
        club1 = Club(name='Nexus Coding Club', description='Developing awesome apps and participating in global hackathons.', campus_id=campus.id, lat=42.3605, lng=-71.0938)
        club2 = Club(name='Robotics & AI Lab', description='Building autonomous robots and exploring neural networks.', campus_id=campus.id, lat=42.3598, lng=-71.0948)
        db.session.add_all([club1, club2])

        office1 = Office(name='Registrar Office', description='For all academic records, course enrollment, and transcripts.', campus_id=campus.id, lat=42.3602, lng=-71.0940)
        office2 = Office(name='Student Services Center', description='Providing health, housing, and general support for students.', campus_id=campus.id, lat=42.3600, lng=-71.0945)
        db.session.add_all([office1, office2])
        db.session.commit()
        print("Created clubs and offices.")

        # 5. Add Events
        event1 = Event(
            title='Annual Nexus Hackathon',
            description='A 24-hour coding marathon! Bring your best ideas, form teams, and win amazing prizes.',
            campus_id=campus.id,
            creator_id=alice.id,
            date=datetime.utcnow() + timedelta(days=2),
            end_date=datetime.utcnow() + timedelta(days=3),
            lat=42.3605,
            lng=-71.0938
        )
        event2 = Event(
            title='AI & Ethics Seminar',
            description='A panel discussion on the impact of artificial intelligence in education and future careers.',
            campus_id=campus.id,
            creator_id=bob.id,
            date=datetime.utcnow() + timedelta(days=5),
            end_date=datetime.utcnow() + timedelta(days=5, hours=3),
            lat=42.3600,
            lng=-71.0945
        )
        db.session.add_all([event1, event2])
        db.session.commit()
        print("Created events.")

        # 6. Add Chat Room & Messages
        room = ChatRoom(campus_id=campus.id, name='General Discussion')
        db.session.add(room)
        db.session.commit()

        # Add room memberships
        cm1 = ChatMember(user_id=alice.id, room_id=room.id)
        cm2 = ChatMember(user_id=bob.id, room_id=room.id)
        cm3 = ChatMember(user_id=charlie.id, room_id=room.id)
        db.session.add_all([cm1, cm2, cm3])

        # Add initial chat messages
        msg1 = ChatMessage(room_id=room.id, sender_id=alice.id, body="Hey everyone! Welcome to Nexus University's general chat room.")
        msg2 = ChatMessage(room_id=room.id, sender_id=bob.id, body="Hi Alice! Excited to be here. The campus looks amazing!")
        msg3 = ChatMessage(room_id=room.id, sender_id=charlie.id, body="Agreed! Anyone down to form a team for the upcoming Annual Hackathon?")
        db.session.add_all([msg1, msg2, msg3])
        db.session.commit()
        print("Created chat room and populated mock messages.")

        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_db()
