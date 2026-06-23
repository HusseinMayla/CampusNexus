import os
import sys
from datetime import datetime, timedelta
import bcrypt

# Add current directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from app.models import (
    User, UserEmail, Campus, CampusMember, Club, Office, Event,
    EventParticipation, ChatRoom, ChatMember, ChatMessage,
    StudyRoom, StudyRoomMember, StudyRoomMessage, Resource,
    TutorPost, ResourceRequest, Notification
)

def seed_database():
    app = create_app()
    with app.app_context():
        print("=== DATABASE SEEDING PROCESS STARTED ===")
        print("Dropping existing tables to ensure clean state...")
        db.drop_all()
        print("Recreating database tables...")
        db.create_all()

        print("Hashing password 'password123' once for speed optimization...")
        password_hash = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print("Password hashed successfully.")

        # -------------------------------------------------------------
        # 1. Seed Campuses
        # -------------------------------------------------------------
        print("Seeding campuses...")
        campuses_data = [
            {
                "name": "American University of Beirut",
                "domain": "aub.edu.lb",
                "description": "A prestigious private, non-sectarian, and independent university in Beirut, Lebanon.",
                "center_lat": 33.8996,
                "center_lng": 35.4793,
                "banner_image": None,
                "map_image": None
            },
            {
                "name": "Lebanese American University",
                "domain": "lau.edu.lb",
                "description": "A leading private, non-sectarian higher education institution in Lebanon, operating campuses in Beirut and Byblos.",
                "center_lat": 33.8938,
                "center_lng": 35.4764,
                "banner_image": None,
                "map_image": None
            },
            {
                "name": "Lebanese University",
                "domain": "ul.edu.lb",
                "description": "The only public institution of higher learning in Lebanon, serving students across all regions.",
                "center_lat": 33.8290,
                "center_lng": 35.5262,
                "banner_image": None,
                "map_image": None
            },
            {
                "name": "Massachusetts Institute of Technology",
                "domain": "mit.edu",
                "description": "A world-renowned private research university in Cambridge, Massachusetts, dedicated to science, technology, and engineering.",
                "center_lat": 42.3601,
                "center_lng": -71.0942,
                "banner_image": None,
                "map_image": None
            },
            {
                "name": "Stanford University",
                "domain": "stanford.edu",
                "description": "A prominent private research university in Stanford, California, known for its academic strength, wealth, and proximity to Silicon Valley.",
                "center_lat": 37.4275,
                "center_lng": -122.1697,
                "banner_image": None,
                "map_image": None
            }
        ]

        campuses = []
        for c_data in campuses_data:
            c = Campus(
                name=c_data["name"],
                domain=c_data["domain"],
                description=c_data["description"],
                center_lat=c_data["center_lat"],
                center_lng=c_data["center_lng"],
                banner_image=c_data["banner_image"],
                map_image=c_data["map_image"]
            )
            db.session.add(c)
            campuses.append(c)

        # Flush to get campus IDs
        db.session.flush()
        print(f"Campuses seeded: {[c.name for c in campuses]}")

        # -------------------------------------------------------------
        # 2. Seed Users (Exactly 30 Users)
        # -------------------------------------------------------------
        print("Seeding 30 diverse user accounts...")
        users_data = [
            ("Hussein Mayla", "hussein@aub.edu.lb", [("lau.edu.lb", "hussein.sec@lau.edu.lb"), ("ul.edu.lb", "hussein.sec2@ul.edu.lb")]),
            ("Alice Smith", "alice@lau.edu.lb", [("aub.edu.lb", "alice.sec@aub.edu.lb"), ("mit.edu", "alice.sec2@mit.edu")]),
            ("Bob Jones", "bob@ul.edu.lb", [("lau.edu.lb", "bob.sec@lau.edu.lb"), ("stanford.edu", "bob.sec2@stanford.edu")]),
            ("Charlie Brown", "charlie@mit.edu", [("stanford.edu", "charlie.sec@stanford.edu"), ("aub.edu.lb", "charlie.sec2@aub.edu.lb")]),
            ("Diana Prince", "diana@stanford.edu", [("mit.edu", "diana.sec@mit.edu"), ("aub.edu.lb", "diana.sec2@aub.edu.lb")]),
            ("Evan Wright", "evan@aub.edu.lb", [("ul.edu.lb", "evan.sec@ul.edu.lb"), ("lau.edu.lb", "evan.sec2@lau.edu.lb")]),
            ("Fiona Gallagher", "fiona@lau.edu.lb", [("aub.edu.lb", "fiona.sec@aub.edu.lb"), ("ul.edu.lb", "fiona.sec2@ul.edu.lb")]),
            ("George Costanza", "george@ul.edu.lb", [("mit.edu", "george.sec@mit.edu"), ("stanford.edu", "george.sec2@stanford.edu")]),
            ("Hannah Baker", "hannah@mit.edu", [("stanford.edu", "hannah.sec@stanford.edu"), ("lau.edu.lb", "hannah.sec2@lau.edu.lb")]),
            ("Ian Malcolm", "ian@stanford.edu", [("mit.edu", "ian.sec@mit.edu"), ("ul.edu.lb", "ian.sec2@ul.edu.lb")]),
            ("Julia Roberts", "julia@aub.edu.lb", [("lau.edu.lb", "julia.sec@lau.edu.lb"), ("mit.edu", "julia.sec2@mit.edu")]),
            ("Kevin Bacon", "kevin@lau.edu.lb", [("ul.edu.lb", "kevin.sec@ul.edu.lb"), ("stanford.edu", "kevin.sec2@stanford.edu")]),
            ("Laura Croft", "laura@ul.edu.lb", [("aub.edu.lb", "laura.sec@aub.edu.lb"), ("stanford.edu", "laura.sec2@stanford.edu")]),
            ("Michael Scott", "michael@mit.edu", [("stanford.edu", "michael.sec@stanford.edu"), ("aub.edu.lb", "michael.sec2@aub.edu.lb")]),
            ("Nina Simone", "nina@stanford.edu", [("mit.edu", "nina.sec@mit.edu"), ("lau.edu.lb", "nina.sec2@lau.edu.lb")]),
            ("Oscar Martinez", "oscar@aub.edu.lb", [("ul.edu.lb", "oscar.sec@ul.edu.lb"), ("lau.edu.lb", "oscar.sec2@lau.edu.lb")]),
            ("Pam Beesly", "pam@lau.edu.lb", [("aub.edu.lb", "pam.sec@aub.edu.lb"), ("mit.edu", "pam.sec2@mit.edu")]),
            ("Quentin Tarantino", "quentin@ul.edu.lb", [("stanford.edu", "quentin.sec@stanford.edu"), ("lau.edu.lb", "quentin.sec2@lau.edu.lb")]),
            ("Rachel Green", "rachel@mit.edu", [("lau.edu.lb", "rachel.sec@lau.edu.lb"), ("stanford.edu", "rachel.sec2@stanford.edu")]),
            ("Steve Rogers", "steve@stanford.edu", [("mit.edu", "steve.sec@mit.edu"), ("aub.edu.lb", "steve.sec2@aub.edu.lb")]),
            ("Tony Stark", "tony@aub.edu.lb", [("mit.edu", "tony.sec@mit.edu"), ("lau.edu.lb", "tony.sec2@lau.edu.lb")]),
            ("Ursula Buffay", "ursula@lau.edu.lb", [("ul.edu.lb", "ursula.sec@ul.edu.lb"), ("stanford.edu", "ursula.sec2@stanford.edu")]),
            ("Victor Von Doom", "victor@ul.edu.lb", [("mit.edu", "victor.sec@mit.edu"), ("stanford.edu", "victor.sec2@stanford.edu")]),
            ("Wanda Maximoff", "wanda@mit.edu", [("stanford.edu", "wanda.sec@stanford.edu"), ("aub.edu.lb", "wanda.sec2@aub.edu.lb")]),
            ("Xavier Charles", "xavier@stanford.edu", [("aub.edu.lb", "xavier.sec@aub.edu.lb"), ("lau.edu.lb", "xavier.sec2@lau.edu.lb")]),
            ("Youssef Kanaan", "youssef@aub.edu.lb", [("ul.edu.lb", "youssef.sec@ul.edu.lb"), ("lau.edu.lb", "youssef.sec2@lau.edu.lb")]),
            ("Zoe Saldana", "zoe@lau.edu.lb", [("aub.edu.lb", "zoe.sec@aub.edu.lb"), ("stanford.edu", "zoe.sec2@stanford.edu")]),
            ("Arthur Pendragon", "arthur@ul.edu.lb", [("lau.edu.lb", "arthur.sec@lau.edu.lb"), ("mit.edu", "arthur.sec2@mit.edu")]),
            ("Bruce Wayne", "bruce@mit.edu", [("stanford.edu", "bruce.sec@stanford.edu"), ("aub.edu.lb", "bruce.sec2@aub.edu.lb")]),
            ("Clark Kent", "clark@stanford.edu", [("mit.edu", "clark.sec@mit.edu"), ("ul.edu.lb", "clark.sec2@ul.edu.lb")]),
        ]

        users = []
        user_secondary_emails = {} # Maps user email -> list of secondary (domain, email) tuples
        
        for name, email, secondary_list in users_data:
            u = User(
                name=name,
                email=email,
                password_hash=password_hash,
                is_verified=True
            )
            db.session.add(u)
            users.append(u)
            user_secondary_emails[email] = secondary_list

        db.session.flush() # Flush to get User IDs

        # Add creator locks to campuses
        # Hussein -> AUB, Alice -> LAU, Bob -> LU, Charlie -> MIT, Diana -> Stanford
        campuses[0].creator_id = users[0].id # AUB -> Hussein
        campuses[1].creator_id = users[1].id # LAU -> Alice
        campuses[2].creator_id = users[2].id # LU -> Bob
        campuses[3].creator_id = users[3].id # MIT -> Charlie
        campuses[4].creator_id = users[4].id # Stanford -> Diana
        db.session.flush()

        # -------------------------------------------------------------
        # 3. Seed CampusMemberships (2-3 campuses per user maximum)
        # -------------------------------------------------------------
        print("Establishing multi-campus memberships and roles...")
        
        # Helper map of domain -> campus object
        domain_to_campus = {c.domain: c for c in campuses}

        for u in users:
            # Determine which primary campus the user belongs to
            primary_domain = u.email.split('@')[1]
            primary_campus = domain_to_campus[primary_domain]
            
            # Primary membership
            # If the user is the creator, they are the 'owner'. Otherwise, let's make 2 of them admins and others users.
            role = 'user'
            if primary_campus.creator_id == u.id:
                role = 'owner'
            elif u.name in ["Tony Stark", "Steve Rogers", "Victor Von Doom", "Wanda Maximoff"]:
                role = 'admin'

            db.session.add(CampusMember(user_id=u.id, campus_id=primary_campus.id, role=role))

            # Secondary memberships (adds secondary verified email, then joins campus)
            sec_list = user_secondary_emails[u.email]
            for sec_domain, sec_email in sec_list:
                sec_campus = domain_to_campus[sec_domain]
                
                # Add verified secondary email
                db.session.add(UserEmail(
                    user_id=u.id,
                    email=sec_email,
                    is_verified=True
                ))
                
                # Join the secondary campus as a standard user
                db.session.add(CampusMember(
                    user_id=u.id,
                    campus_id=sec_campus.id,
                    role='user'
                ))

        db.session.flush()
        print("Memberships and secondary verified emails created successfully.")

        # Helper functions to get all members of a campus
        def get_campus_members(campus_id):
            return [m.user_id for m in CampusMember.query.filter_by(campus_id=campus_id).all()]

        # -------------------------------------------------------------
        # 4. Seed Clubs & Offices
        # -------------------------------------------------------------
        print("Seeding Clubs and Offices on Campus Maps...")
        for c in campuses:
            lat, lng = c.center_lat, c.center_lng
            
            # Add 2 clubs
            db.session.add(Club(
                name="Computer Science & AI Club",
                description=f"Connecting tech enthusiasts, programmers, and AI hobbyists at {c.name}.",
                campus_id=c.id,
                lat=lat + 0.0008,
                lng=lng + 0.0006
            ))
            db.session.add(Club(
                name="Music & Performing Arts Club",
                description=f"A home for musicians, singers, actors, and artists to practice, collaborate, and perform at {c.name}.",
                campus_id=c.id,
                lat=lat - 0.0007,
                lng=lng - 0.0005
            ))

            # Add 2 offices
            db.session.add(Office(
                name="Admissions & Registrar Office",
                description="Handling enrollment, transcripts, transfer credits, and general academic scheduling.",
                campus_id=c.id,
                lat=lat + 0.0003,
                lng=lng - 0.0004
            ))
            db.session.add(Office(
                name="Student Affairs & Wellness Center",
                description="Promoting student engagement, mental health counseling, athletics, and community support.",
                campus_id=c.id,
                lat=lat - 0.0004,
                lng=lng + 0.0003
            ))

        db.session.flush()

        # -------------------------------------------------------------
        # 5. Seed Events & Participations
        # -------------------------------------------------------------
        print("Seeding Events and User Participations...")
        now = datetime.utcnow()
        
        events = []
        for i, c in enumerate(campuses):
            # Event 1: Today (Spring Fest)
            e1 = Event(
                title=f"{c.name} Spring Festival",
                description="A campus-wide celebration featuring live music, food trucks, game booths, and cultural performances. Don't miss it!",
                campus_id=c.id,
                creator_id=c.creator_id,
                date=now.replace(hour=14, minute=0, second=0),
                end_date=now.replace(hour=20, minute=0, second=0),
                lat=c.center_lat + 0.0002,
                lng=c.center_lng - 0.0002
            )
            # Event 2: Tomorrow (Hackathon)
            e2 = Event(
                title="Annual Tech Hackathon",
                description="48 hours of pure coding, design, and product pitch development! Teams will build solutions addressing sustainability and campus life.",
                campus_id=c.id,
                creator_id=c.creator_id,
                date=now + timedelta(days=1, hours=2),
                end_date=now + timedelta(days=3, hours=2),
                lat=c.center_lat - 0.0003,
                lng=c.center_lng + 0.0003
            )
            # Event 3: Next Week (Career Fair)
            e3 = Event(
                title="Spring 2026 Career Fair",
                description="Meet recruiters from top local and multinational companies. Bring your resumes, dress professionally, and secure internships or full-time roles!",
                campus_id=c.id,
                creator_id=c.creator_id,
                date=now + timedelta(days=7),
                end_date=now + timedelta(days=7, hours=6),
                lat=c.center_lat + 0.0004,
                lng=c.center_lng + 0.0004
            )
            db.session.add_all([e1, e2, e3])
            events.extend([e1, e2, e3])

        db.session.flush()

        # Add event participations (interested / want notification)
        for e in events:
            # Get members of this campus
            member_ids = get_campus_members(e.campus_id)
            # Mark first 5-8 members as interested
            for uid in member_ids[:8]:
                db.session.add(EventParticipation(
                    event_id=e.id,
                    user_id=uid,
                    is_interested=True,
                    want_notification=True,
                    notification_sent=False
                ))

        db.session.flush()

        # -------------------------------------------------------------
        # 6. Seed ChatRooms, Members & Messages
        # -------------------------------------------------------------
        print("Seeding Campus Chat Rooms and Chat Messages...")
        chat_messages_pool = [
            "Hey everyone! Welcome to the new campus portal.",
            "Wow, this is so smooth. Love the map integrations!",
            "Anyone down to study in the library later today?",
            "Yes, I'm heading there around 3 PM.",
            "Which floor? Let's book a study room.",
            "Usually 2nd floor, near the CS wing.",
            "Awesome, see you there!",
            "Did anyone start the CS project yet?",
            "Working on it right now. The database constraints are tricky.",
            "Tell me about it... Took me two hours to debug the migration.",
            "Let's schedule a study session tomorrow to align."
        ]

        for c in campuses:
            # Create two chatrooms per campus
            r1 = ChatRoom(campus_id=c.id, name="general")
            r2 = ChatRoom(campus_id=c.id, name="study-help")
            db.session.add_all([r1, r2])
            db.session.flush()

            # Join all campus members to both rooms
            member_ids = get_campus_members(c.id)
            for uid in member_ids:
                db.session.add(ChatMember(user_id=uid, room_id=r1.id))
                db.session.add(ChatMember(user_id=uid, room_id=r2.id))

            db.session.flush()

            # Add chat messages
            for idx, msg_text in enumerate(chat_messages_pool):
                sender_id = member_ids[idx % len(member_ids)]
                sent_at = now - timedelta(hours=len(chat_messages_pool) - idx)
                # Alternate between general and study-help
                room_id = r1.id if idx % 2 == 0 else r2.id
                db.session.add(ChatMessage(
                    room_id=room_id,
                    sender_id=sender_id,
                    body=msg_text,
                    sent_at=sent_at
                ))

        db.session.flush()

        # -------------------------------------------------------------
        # 7. Seed StudyRooms, Members & Messages
        # -------------------------------------------------------------
        print("Seeding Study Rooms and Messages...")
        study_msg_pool = [
            "Hey, thanks for creating this study group!",
            "Happy to help! Let's cover Chapters 3 and 4 today.",
            "I'm really struggling with the recursive relations part.",
            "Don't worry, we can sketch it out on the whiteboard.",
            "Awesome, I'm on my way now."
        ]

        for c in campuses:
            member_ids = get_campus_members(c.id)
            if len(member_ids) < 3:
                continue

            owner_id = member_ids[0]
            
            # Study Room 1: Active soon (Calculus I Prep)
            sr1 = StudyRoom(
                campus_id=c.id,
                owner_id=owner_id,
                title="MATH 201 Midterm Prep",
                location="Library 2nd Floor, Room B",
                session_time=now + timedelta(hours=3),
                max_members=8
            )
            # Study Room 2: Upcoming (CS Project Collaboration)
            sr2 = StudyRoom(
                campus_id=c.id,
                owner_id=member_ids[1],
                title="CS101 Project Sprint",
                location="Tech Wing Hub",
                session_time=now + timedelta(days=1, hours=1),
                max_members=6
            )
            db.session.add_all([sr1, sr2])
            db.session.flush()

            # Join members
            # Room 1: owner + 2 members
            db.session.add(StudyRoomMember(room_id=sr1.id, user_id=owner_id))
            db.session.add(StudyRoomMember(room_id=sr1.id, user_id=member_ids[1]))
            db.session.add(StudyRoomMember(room_id=sr1.id, user_id=member_ids[2]))
            
            # Room 2: owner + 1 member
            db.session.add(StudyRoomMember(room_id=sr2.id, user_id=member_ids[1]))
            db.session.add(StudyRoomMember(room_id=sr2.id, user_id=member_ids[0]))

            db.session.flush()

            # Add study messages for Room 1
            for idx, msg_text in enumerate(study_msg_pool):
                sender_id = member_ids[idx % 3] # Rotate among the 3 joined members
                sent_at = now - timedelta(minutes=30 - idx * 5)
                db.session.add(StudyRoomMessage(
                    room_id=sr1.id,
                    sender_id=sender_id,
                    body=msg_text,
                    sent_at=sent_at
                ))

        db.session.flush()

        # -------------------------------------------------------------
        # 8. Seed Resources, TutorPosts & ResourceRequests
        # -------------------------------------------------------------
        print("Seeding Academic Resources, Tutor Posts, and Resource Requests...")
        
        # Ensure uploads directories exist so downloading/deleting works flawlessly
        resources_dir = os.path.join(app.static_folder, 'uploads', 'resources')
        os.makedirs(resources_dir, exist_ok=True)

        # Create physical dummy files so download and deletes work!
        dummy_resources = [
            ("cs101_syllabus.pdf", "CS101 Course Syllabus and Project Rubrics"),
            ("math201_past_midterm.pdf", "Calculus I Midterm past exam with solution sheet."),
            ("physics_ch1_slides.pptx", "Introductory Physics Lecture 1 Slides (Motion in 1D).")
        ]
        
        for filename, desc in dummy_resources:
            filepath = os.path.join(resources_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w') as f:
                    f.write(f"CampusNexus Seeded Mock Resource File:\nDescription: {desc}")

        for c in campuses:
            member_ids = get_campus_members(c.id)
            if not member_ids:
                continue
            
            uploader_id = member_ids[0]

            # 3 Resources per campus
            r1 = Resource(
                title="CS101 Course Syllabus",
                description="Comprehensive syllabus detailing lecture schedule, grading criteria, and project deadlines.",
                file_url="uploads/resources/cs101_syllabus.pdf",
                campus_id=c.id,
                uploader_id=uploader_id,
                course_code="CS101",
                chapters="1-12",
                file_type="pdf",
                original_filename="cs101_syllabus.pdf"
            )
            r2 = Resource(
                title="Calculus I Past Midterm Exam",
                description="Detailed midterm practice exam with step-by-step solutions for derivatives and integration.",
                file_url="uploads/resources/math201_past_midterm.pdf",
                campus_id=c.id,
                uploader_id=uploader_id,
                course_code="MATH201",
                chapters="Chapters 1-4",
                file_type="pdf",
                original_filename="math201_past_midterm.pdf"
            )
            r3 = Resource(
                title="Physics Ch1 Lecture Slides",
                description="Official lecture slides covering vectors, velocity, and introductory kinematics.",
                file_url="uploads/resources/physics_ch1_slides.pptx",
                campus_id=c.id,
                uploader_id=uploader_id,
                course_code="PHYS101",
                chapters="Chapter 1",
                file_type="pptx",
                original_filename="physics_ch1_slides.pptx"
            )
            db.session.add_all([r1, r2, r3])

            # 2 Tutor Posts per campus
            tp1 = TutorPost(
                campus_id=c.id,
                poster_id=member_ids[0],
                full_name=users[0].name if uploader_id == users[0].id else "Senior Peer Tutor",
                email="peer.tutor@example.com",
                role="tutor",
                courses="CS101, MATH201",
                method="online"
            )
            tp2 = TutorPost(
                campus_id=c.id,
                poster_id=member_ids[1 % len(member_ids)],
                full_name="Graduate Assistant",
                email="grad.assistant@example.com",
                role="tutor",
                courses="PHYS101, CHEM101",
                method="in-person"
            )
            db.session.add_all([tp1, tp2])

            # 2 Resource Requests per campus
            rr1 = ResourceRequest(
                campus_id=c.id,
                poster_id=member_ids[0],
                email="student.req@example.com",
                course_code="MATH201",
                chapters="Chapter 5 (Integration)"
            )
            rr2 = ResourceRequest(
                campus_id=c.id,
                poster_id=member_ids[1 % len(member_ids)],
                email="student.req2@example.com",
                course_code="CS101",
                chapters="Chapter 8 (Object-Oriented Programming)"
            )
            db.session.add_all([rr1, rr2])

        db.session.flush()

        # -------------------------------------------------------------
        # 9. Seed Notifications
        # -------------------------------------------------------------
        print("Seeding active dashboard notifications for key users...")
        
        # Add notifications for key active users so their feeds show rich content
        target_users = users[:5] # Hussein, Alice, Bob, Charlie, Diana
        for u in target_users:
            n1 = Notification(
                user_id=u.id,
                title="Welcome to CampusNexus!",
                message=f"Hi {u.name}, welcome to Agora's CampusNexus! Discover campuses, join chatrooms, map resources, and prepare for upcoming study groups.",
                is_read=False,
                link="/"
            )
            n2 = Notification(
                user_id=u.id,
                title="📅 Spring Festival starts today!",
                message="The Spring Festival has officially kicked off! Head to the campus map to locate the events.",
                is_read=False,
                link="/campus/1/chat"
            )
            n3 = Notification(
                user_id=u.id,
                title="📝 New Resource Uploaded",
                message="A new resource has been uploaded for MATH201: 'Calculus I Past Midterm Exam'. Check it out in resources!",
                is_read=True, # Pre-marked as read
                link="/campus/1/resources"
            )
            db.session.add_all([n1, n2, n3])

        print("Finalizing database transaction commits...")
        db.session.commit()
        print("=== DATABASE SEEDING COMPLETED SUCCESSFULLY ===")
        print("30 users, 5 campuses, and all connected models successfully populated.")

if __name__ == '__main__':
    seed_database()
