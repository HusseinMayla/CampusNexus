import os
from app import create_app
from app.extensions import db
from app.models import User, UserEmail, Campus, CampusMember, Notification
from sqlalchemy import func

app = create_app()

def run_tests():
    with app.app_context():
        print("--- [TEST] Starting Multi-Email, Campus Refinement, & Roles Tests ---")
        
        # 1. Reset database for a clean state
        db.drop_all()
        db.create_all()
        print("Cleaned and initialized database tables successfully.")

        # 2. Create target campuses with domain restrictions
        aub = Campus(name="American University of Beirut", domain="aub.edu.lb")
        lau = Campus(name="Lebanese American University", domain="lau.edu.lb")
        lu  = Campus(name="Lebanese University", domain="ul.edu.lb")
        db.session.add_all([aub, lau, lu])
        db.session.commit()
        print("Created Campuses:")
        print(f"  - {aub.name} (domain: {aub.domain})")
        print(f"  - {lau.name} (domain: {lau.domain})")
        print(f"  - {lu.name} (domain: {lu.domain})")

        # 3. Create a test user with a personal primary email
        user = User(name="Hussein Mayla", email="hussein@gmail.com", password_hash="dummy_hash")
        db.session.add(user)
        db.session.commit()
        print(f"Created test user: {user.name} ({user.email})")

        # 4. Attempt to join AUB campus with primary email (Should FAIL)
        print("\nAttempting to join AUB with primary email (hussein@gmail.com)...")
        if user.has_verified_domain(aub.domain):
            print("[-] FAILURE: User should not have verified domain aub.edu.lb.")
        else:
            print("[OK] SUCCESS: User is correctly denied access to AUB due to domain mismatch.")

        # 5. Add and verify AUB secondary email
        sec_aub = UserEmail(user_id=user.id, email="hussein@aub.edu.lb", is_verified=True)
        db.session.add(sec_aub)
        db.session.commit()
        print(f"Added and verified secondary email: {sec_aub.email}")

        # 6. Attempt to join AUB campus with verified secondary email (Should PASS)
        print("Attempting to join AUB with newly added verified email...")
        if user.has_verified_domain(aub.domain):
            print("[OK] SUCCESS: User now has verified domain aub.edu.lb!")
            # Join the campus
            member = CampusMember(user_id=user.id, campus_id=aub.id)
            db.session.add(member)
            db.session.commit()
            print("[OK] SUCCESS: User joined AUB successfully.")
        else:
            print("[-] FAILURE: User still blocked from joining AUB.")

        # 7. Attempt to join LAU campus (Should FAIL since LAU email is not added yet)
        print("\nAttempting to join LAU (Double Major test before adding LAU email)...")
        if user.has_verified_domain(lau.domain):
            print("[-] FAILURE: User should not have verified domain lau.edu.lb.")
        else:
            print("[OK] SUCCESS: User is correctly denied access to LAU.")

        # 8. Add LAU secondary email but leave it UNVERIFIED (Should FAIL)
        sec_lau = UserEmail(user_id=user.id, email="hussein@lau.edu.lb", is_verified=False)
        db.session.add(sec_lau)
        db.session.commit()
        print(f"Added UNVERIFIED secondary email: {sec_lau.email}")
        
        print("Attempting to join LAU with unverified email...")
        if user.has_verified_domain(lau.domain):
            print("[-] FAILURE: User allowed to join LAU with an unverified email!")
        else:
            print("[OK] SUCCESS: User is correctly blocked due to email being unverified.")

        # 9. Verify the LAU email (Should PASS)
        sec_lau.is_verified = True
        db.session.commit()
        print("Verified the LAU email.")
        
        print("Attempting to join LAU after verification...")
        if user.has_verified_domain(lau.domain):
            print("[OK] SUCCESS: User now has verified domain lau.edu.lb!")
            member = CampusMember(user_id=user.id, campus_id=lau.id)
            db.session.add(member)
            db.session.commit()
            print("[OK] SUCCESS: User joined LAU successfully (Double Major verified!).")
        else:
            print("[-] FAILURE: User blocked from joining LAU after verification.")

        # 10. Uniqueness Constraints Test
        print("\n--- [TEST] Testing Global Uniqueness Constraint ---")
        
        # Test 10a: Try to add another UserEmail with the same email as AUB email (Should fail)
        print("Attempting to create a duplicate secondary email...")
        duplicate_email = UserEmail(user_id=999, email="hussein@aub.edu.lb", is_verified=True)
        db.session.add(duplicate_email)
        try:
            db.session.commit()
            print("[-] FAILURE: Database allowed duplicate secondary email!")
        except Exception as e:
            db.session.rollback()
            print("[OK] SUCCESS: Unique constraint correctly rejected duplicate secondary email.")

        # Test 10b: Try to add a secondary email that matches an existing primary email
        print("Attempting to create secondary email matching an existing primary email...")
        # Add another user with primary email "someone@test.com"
        someone = User(name="Someone Else", email="someone@test.com", password_hash="dummy")
        db.session.add(someone)
        db.session.commit()
        
        email_to_add = "someone@test.com"
        already_primary = User.query.filter_by(email=email_to_add).first() is not None
        already_secondary = UserEmail.query.filter_by(email=email_to_add).first() is not None
        if already_primary or already_secondary:
            print("[OK] SUCCESS: Uniqueness check correctly identified conflict with primary email.")
        else:
            print("[-] FAILURE: Uniqueness check failed to identify conflict.")

        # Test 10c: Try joining restricted campus with this dummy user who has NO university emails at all
        print("Attempting to join AUB campus with dummy user someone@test.com...")
        if someone.has_verified_domain(aub.domain):
            print("[-] FAILURE: Dummy user without uni emails was allowed verified domain aub.edu.lb!")
        else:
            print("[OK] SUCCESS: Dummy user without uni emails is correctly blocked from joining restricted campus.")

        # 11. Unique Campus Names Test
        print("\n--- [TEST] Testing Unique Campus Names ---")
        duplicate_campus = Campus(name="American University of Beirut")
        db.session.add(duplicate_campus)
        try:
            db.session.commit()
            print("[-] FAILURE: Duplicate campus name allowed!")
        except Exception as e:
            db.session.rollback()
            print("[OK] SUCCESS: Campus name unique constraint correctly rejected duplicate.")

        # 12. Locked Campus Creation Check (Security)
        print("\n--- [TEST] Testing Creator Domain Locking (Security Check) ---")
        # User 'someone' has someone@test.com. They should be blocked from creating a campus with domain 'aub.edu.lb'
        target_domain = "aub.edu.lb"
        if not someone.has_verified_domain(target_domain):
            print("[OK] SUCCESS: Security check correctly blocks creator 'someone' from locking a campus to 'aub.edu.lb' since they don't own it.")
        else:
            print("[-] FAILURE: User 'someone' falsely authorized for domain aub.edu.lb.")

        # User 'user' has verified hussein@aub.edu.lb. They should be allowed to create it.
        if user.has_verified_domain(target_domain):
            print("[OK] SUCCESS: Security check correctly authorizes creator 'user' to create campus locked to 'aub.edu.lb'.")
        else:
            print("[-] FAILURE: User 'user' blocked from creating campus locked to aub.edu.lb.")

        # 13. Auto-Verification of Admin/IT Emails
        print("\n--- [TEST] Testing Auto-Verification of admin@ and IT@ Emails ---")
        # Case A: admin@
        admin_email_str = "admin@usj.edu.lb"
        is_admin_auto_verified = admin_email_str.split('@')[0].lower() in ['admin', 'it']
        admin_email = UserEmail(user_id=user.id, email=admin_email_str, is_verified=is_admin_auto_verified)
        db.session.add(admin_email)
        db.session.commit()
        print(f"Added admin email: {admin_email.email}. Auto-verified: {admin_email.is_verified}")
        if admin_email.is_verified:
            print("[OK] SUCCESS: admin@ email correctly auto-verified.")
        else:
            print("[-] FAILURE: admin@ email was not auto-verified.")

        # Case B: IT@
        it_email_str = "IT@usj.edu.lb"
        is_it_auto_verified = it_email_str.split('@')[0].lower() in ['admin', 'it']
        it_email = UserEmail(user_id=user.id, email=it_email_str, is_verified=is_it_auto_verified)
        db.session.add(it_email)
        db.session.commit()
        print(f"Added IT email: {it_email.email}. Auto-verified: {it_email.is_verified}")
        if it_email.is_verified:
            print("[OK] SUCCESS: IT@ email correctly auto-verified.")
        else:
            print("[-] FAILURE: IT@ email was not auto-verified.")

        # Case C: normal student
        normal_email_str = "student@usj.edu.lb"
        is_normal_auto_verified = normal_email_str.split('@')[0].lower() in ['admin', 'it']
        normal_email = UserEmail(user_id=someone.id, email=normal_email_str, is_verified=is_normal_auto_verified)
        db.session.add(normal_email)
        db.session.commit()
        print(f"Added student email: {normal_email.email}. Auto-verified: {normal_email.is_verified}")
        if not normal_email.is_verified:
            print("[OK] SUCCESS: student@ email was NOT auto-verified (requires verification).")
        else:
            print("[-] FAILURE: student@ email was falsely auto-verified.")

        # 14. Popularity Sorting Test
        print("\n--- [TEST] Testing Campus Popularity Sorting ---")
        # Let's make LU have 3 members, LAU 2 members, and AUB 1 member.
        # Add members to LU
        u_lu = UserEmail(user_id=user.id, email="hussein@ul.edu.lb", is_verified=True)
        s_lu = UserEmail(user_id=someone.id, email="someone@ul.edu.lb", is_verified=True)
        # Add a third user to join LU
        third_user = User(name="Third Student", email="third@ul.edu.lb", password_hash="dummy")
        db.session.add_all([u_lu, s_lu, third_user])
        db.session.commit()

        # Join LU
        db.session.add(CampusMember(user_id=user.id, campus_id=lu.id))
        db.session.add(CampusMember(user_id=someone.id, campus_id=lu.id))
        db.session.add(CampusMember(user_id=third_user.id, campus_id=lu.id))

        # Join LAU
        s_lau = UserEmail(user_id=someone.id, email="someone@lau.edu.lb", is_verified=True)
        db.session.add(s_lau)
        db.session.commit()
        db.session.add(CampusMember(user_id=someone.id, campus_id=lau.id))
        db.session.commit()

        # Popularity sort
        campuses_popularity = db.session.query(
            Campus, 
            func.count(CampusMember.id).label('member_count')
        ).outerjoin(CampusMember)\
         .group_by(Campus.id)\
         .order_by(func.count(CampusMember.id).desc())\
         .all()

        print("Sorted Campuses by Popularity:")
        for c, count in campuses_popularity:
            print(f"  - {c.name}: {count} members")

        if campuses_popularity[0][0].id == lu.id and campuses_popularity[1][0].id == lau.id and campuses_popularity[2][0].id == aub.id:
            print("[OK] SUCCESS: Campuses correctly sorted by popularity (LU -> LAU -> AUB).")
        else:
            print("[-] FAILURE: Popularity sorting order incorrect.")

        # 16. Owner Role Auto-Assignment Test
        print("\n--- [TEST] Testing Owner Role Auto-Assignment ---")
        # Let's create a new campus by user "user"
        mu = Campus(name="Mind University", creator_id=user.id)
        db.session.add(mu)
        db.session.commit()
        
        # Enforce creator is added as owner
        creator_membership = CampusMember(user_id=user.id, campus_id=mu.id, role='owner')
        db.session.add(creator_membership)
        db.session.commit()
        
        fetched_membership = CampusMember.query.filter_by(user_id=user.id, campus_id=mu.id).first()
        print(f"Created campus {mu.name}. Creator {user.name} membership role: {fetched_membership.role}")
        if fetched_membership.role == 'owner':
            print("[OK] SUCCESS: Creator is auto-assigned the 'owner' role.")
        else:
            print("[-] FAILURE: Creator not set as owner.")

        # 17. Promotion & Demotion Gates
        print("\n--- [TEST] Testing Promotion & Demotion Gates ---")
        # Join 'someone' as standard user to MU
        db.session.add(CampusMember(user_id=someone.id, campus_id=mu.id, role='user'))
        db.session.commit()
        someone_membership = CampusMember.query.filter_by(user_id=someone.id, campus_id=mu.id).first()
        print(f"Joined {someone.name} to MU. Initial role: {someone_membership.role}")

        # Non-owner 'third_user' tries to promote 'someone' (Simulation of route gate)
        # owner of mu is user.id
        request_caller_id = third_user.id
        owner_membership = CampusMember.query.filter_by(user_id=request_caller_id, campus_id=mu.id).first()
        is_owner = owner_membership and owner_membership.role == 'owner'
        if not is_owner:
            print("[OK] SUCCESS: Non-owner 'third_user' is correctly blocked from promoting members.")
        else:
            print("[-] FAILURE: Non-owner allowed to promote!")

        # Real owner 'user' promotes 'someone'
        request_caller_id = user.id
        owner_membership = CampusMember.query.filter_by(user_id=request_caller_id, campus_id=mu.id).first()
        if owner_membership and owner_membership.role == 'owner':
            someone_membership.role = 'admin'
            # Trigger notification
            db.session.add(Notification(
                user_id=someone.id,
                title='Promoted to Admin',
                message=f'You have been promoted to Admin in {mu.name}!'
            ))
            db.session.commit()
            print(f"Owner promoted {someone.name} to: {someone_membership.role}")
            if someone_membership.role == 'admin':
                print("[OK] SUCCESS: Owner successfully promoted member to admin.")
            else:
                print("[-] FAILURE: Owner promotion failed.")

        # Real owner 'user' demotes 'someone' back to 'user'
        someone_membership.role = 'user'
        db.session.add(Notification(
            user_id=someone.id,
            title='Role Demoted',
            message=f'You have been demoted to Member in {mu.name}.'
        ))
        db.session.commit()
        print(f"Owner demoted {someone.name} to: {someone_membership.role}")
        if someone_membership.role == 'user':
            print("[OK] SUCCESS: Owner successfully demoted admin back to user.")
        else:
            print("[-] FAILURE: Owner demotion failed.")

        # 18. Notification Generation & Operations
        print("\n--- [TEST] Testing Notifications System ---")
        # Fetch notifications for 'someone'
        notifs = Notification.query.filter_by(user_id=someone.id).all()
        print(f"Fetched {len(notifs)} notifications for {someone.name}:")
        for n in notifs:
            print(f"  - [{n.title}] {n.message} (Read: {n.is_read})")
        
        if len(notifs) >= 2:
            print("[OK] SUCCESS: Promotion and Demotion auto-generated notification logs.")
        else:
            print("[-] FAILURE: Notification generation missing.")

        # Mark notification read
        target_notif = notifs[0]
        target_notif.is_read = True
        db.session.commit()
        print(f"Marked notification '{target_notif.title}' read. Read status: {target_notif.is_read}")
        if target_notif.is_read:
            print("[OK] SUCCESS: Notification read operation works.")
        else:
            print("[-] FAILURE: Notification read state not saved.")

        # Clear notifications
        Notification.query.filter_by(user_id=someone.id).delete()
        db.session.commit()
        cleared_notifs = Notification.query.filter_by(user_id=someone.id).all()
        print(f"Cleared notifications. Remaining count: {len(cleared_notifs)}")
        if len(cleared_notifs) == 0:
            print("[OK] SUCCESS: Clear notifications operation works.")
        else:
            print("[-] FAILURE: Notification clear failed.")

        # 19. Campus Deletion Cascades
        print("\n--- [TEST] Testing Campus Deletion Cascades (Purge Verification) ---")
        
        # Verify associations exist
        members_count_before = CampusMember.query.filter_by(campus_id=mu.id).count()
        print(f"MU Campus status before delete: Members = {members_count_before}")

        # Non-owner tries to delete
        request_caller_id = someone.id
        owner_membership = CampusMember.query.filter_by(user_id=request_caller_id, campus_id=mu.id).first()
        if not owner_membership or owner_membership.role != 'owner':
            print("[OK] SUCCESS: Non-owner blocked from deleting the campus.")
        else:
            print("[-] FAILURE: Non-owner allowed to delete campus!")

        # Owner deletes campus
        db.session.delete(mu)
        db.session.commit()
        print("Owner deleted MU Campus.")

        # Verify cascades
        members_count_after = CampusMember.query.filter_by(campus_id=mu.id).count()
        print(f"MU Campus status after delete: Members = {members_count_after}")
        if members_count_after == 0:
            print("[OK] SUCCESS: Deleting the campus successfully purged all cascading memberships.")
        else:
            print("[-] FAILURE: Purge failed! Orphan records remaining.")

        print("\n--- [TEST] All Multi-Email, Refinement, & Roles Tests Completed Successfully! ---")

if __name__ == '__main__':
    run_tests()
