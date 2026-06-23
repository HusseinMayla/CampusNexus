import os
import re
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, send_from_directory, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Campus, CampusMember, Notification, Resource, TutorPost, ResourceRequest, ChatRoom, ChatMember, ChatMessage, Event, EventParticipation
from sqlalchemy import func

main_bp = Blueprint('main', __name__)


def _is_member(campus):
    return (campus.creator_id == current_user.id or
            CampusMember.query.filter_by(user_id=current_user.id, campus_id=campus.id).first() is not None)


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
RESOURCE_EXTENSIONS = {'pdf', 'pptx', 'ppt', 'docx', 'doc', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_resource(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in RESOURCE_EXTENSIONS

@main_bp.route('/')
@main_bp.route('/index')
def index():
    todays_events = []
    joined_campuses_count = 0
    if current_user.is_authenticated:
        joined_campus_ids = [m.campus_id for m in CampusMember.query.filter_by(user_id=current_user.id).all()]
        created_campus_ids = [c.id for c in Campus.query.filter_by(creator_id=current_user.id).all()]
        all_campus_ids = list(set(joined_campus_ids + created_campus_ids))
        joined_campuses_count = len(all_campus_ids)
        
        if all_campus_ids:
            now = datetime.utcnow()
            # Define today as standard UTC calendar day of today
            today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
            today_end = datetime(now.year, now.month, now.day, 23, 59, 59)
            
            # Fetch events for these campuses that start today, sorted by start time
            events = Event.query.filter(
                Event.campus_id.in_(all_campus_ids),
                Event.date >= today_start,
                Event.date <= today_end
            ).order_by(Event.date.asc()).all()
            
            for e in events:
                part_count = EventParticipation.query.filter_by(event_id=e.id, is_interested=True).count()
                user_part = EventParticipation.query.filter_by(event_id=e.id, user_id=current_user.id).first()
                is_interested = False
                if user_part:
                    is_interested = user_part.is_interested
                want_notification = False
                if user_part:
                    want_notification = user_part.want_notification
                is_ended = e.end_date < now
                
                todays_events.append({
                    'event': e,
                    'participation_count': part_count,
                    'is_interested': is_interested,
                    'want_notification': want_notification,
                    'is_ended': is_ended
                })
                
    return render_template(
        'index.html',
        active_page='home',
        todays_events=todays_events,
        joined_campuses_count=joined_campuses_count
    )


@main_bp.route('/dashboard')
@login_required
def dashboard():
    created = Campus.query.filter_by(creator_id=current_user.id).all()
    memberships = CampusMember.query.filter_by(user_id=current_user.id).all()
    joined = []
    for m in memberships:
        joined.append(m.campus)
    campuses = list(created)
    for c in joined:
        if c not in created:
            campuses.append(c)
    created_ids = set()
    for c in created:
        created_ids.add(c.id)
    return render_template('main/dashboard.html', campuses=campuses, created_ids=created_ids)

@main_bp.route('/create-campus', methods=['GET', 'POST'])
@login_required
def create_campus():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        domain = request.form.get('domain', '').strip().lower()

        if not name:
            flash('Campus name is required!', 'error')
            return redirect(url_for('main.create_campus'))

        # Name Uniqueness Check
        existing = Campus.query.filter_by(name=name).first()
        if existing:
            flash('A campus with this name already exists. Please choose a unique name.', 'error')
            return redirect(url_for('main.create_campus'))

        # Clean and validate Domain
        if domain:
            if domain.startswith('@'):
                domain = domain[1:]
                
            # Security / Domain-Lock check: Creator must possess a verified email under this domain
            if not current_user.has_verified_domain(domain):
                flash(f'To restrict this campus to @{domain}, you must first verify an email ending in @{domain}.', 'error')
                return redirect(url_for('main.create_campus'))

        banner_filename = None
        map_filename = None

        # Handle file uploads
        upload_folder = os.path.join(current_app.static_folder, 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        banner_file = request.files.get('banner_image')
        if banner_file and allowed_file(banner_file.filename):
            filename = secure_filename(f"banner_{name}_{banner_file.filename}")
            banner_file.save(os.path.join(upload_folder, filename))
            banner_filename = f"uploads/{filename}"

        map_file = request.files.get('map_image')
        if map_file and allowed_file(map_file.filename):
            filename = secure_filename(f"map_{name}_{map_file.filename}")
            map_file.save(os.path.join(upload_folder, filename))
            map_filename = f"uploads/{filename}"

        if domain:
            campus_domain = domain
        else:
            campus_domain = None

        if banner_filename:
            campus_banner = url_for('static', filename=banner_filename)
        else:
            campus_banner = None

        if map_filename:
            campus_map = url_for('static', filename=map_filename)
        else:
            campus_map = None

        new_campus = Campus(
            name=name,
            description=description,
            domain=campus_domain,
            banner_image=campus_banner,
            map_image=campus_map,
            creator_id=current_user.id
        )
        db.session.add(new_campus)
        db.session.commit()

        # Auto-join creator as owner of their own campus
        db.session.add(CampusMember(user_id=current_user.id, campus_id=new_campus.id, role='owner'))
        db.session.commit()

        flash('Campus created successfully!')
        return redirect(url_for('main.dashboard'))

    return render_template('main/create_campus.html')

@main_bp.route('/join-campus', methods=['GET'])
@login_required
def join_campus():
    # Sort campuses by popularity (member count)
    campuses_with_counts = db.session.query(
        Campus, 
        func.count(CampusMember.id).label('member_count')
    ).outerjoin(CampusMember)\
     .group_by(Campus.id)\
     .order_by(func.count(CampusMember.id).desc())\
     .all()
     
    # Fetch joined ids for current user
    joined_memberships = CampusMember.query.filter_by(user_id=current_user.id).all()
    joined_roles = {}
    for m in joined_memberships:
        joined_roles[m.campus_id] = m.role
    
    campus_list = []
    for campus, count in campuses_with_counts:
        role = joined_roles.get(campus.id)
        if role:
            display_role = role
        elif campus.creator_id == current_user.id:
            display_role = 'owner'
        else:
            display_role = None

        campus_list.append({
            'campus': campus,
            'member_count': count,
            'is_joined': campus.id in joined_roles or campus.creator_id == current_user.id,
            'role': display_role
        })

    return render_template('main/join_campus.html', campuses=campus_list)


@main_bp.route('/campuses/<int:campus_id>/join', methods=['POST'])
@login_required
def join_campus_by_id(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    
    if campus.creator_id == current_user.id:
        flash('You are already the owner of this campus.', 'error')
        return redirect(url_for('main.join_campus'))
        
    already = CampusMember.query.filter_by(user_id=current_user.id, campus_id=campus.id).first()
    if already:
        flash('You have already joined this campus.', 'error')
        return redirect(url_for('main.dashboard'))
        
    # Domain restriction check
    if campus.domain and not current_user.has_verified_domain(campus.domain):
        flash(f'To join this campus, you must verify an email address ending in @{campus.domain}.', 'error')
        return redirect(url_for('main.join_campus'))
        
    # Join
    db.session.add(CampusMember(user_id=current_user.id, campus_id=campus.id, role='user'))
    db.session.commit()
    
    # Notify creator/owner of new member
    if campus.creator_id:
        notif = Notification(
            user_id=campus.creator_id,
            title='New Campus Member',
            message=f'{current_user.name} has joined your campus {campus.name}!',
            link=url_for('main.dashboard')
        )
        db.session.add(notif)
        db.session.commit()
    
    flash(f'You successfully joined {campus.name}!', 'success')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/settings')
@login_required
def settings():
    return render_template('main/settings.html')


@main_bp.route('/campus/<int:campus_id>/settings', methods=['GET', 'POST'])
@login_required
def campus_settings(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    if not current_user.is_campus_owner(campus.id):
        flash('Unauthorized action. Only the campus owner can access campus settings.', 'error')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        domain = request.form.get('domain', '').strip().lower()

        if not name:
            flash('Campus name is required!', 'error')
            return redirect(url_for('main.campus_settings', campus_id=campus.id))

        if name != campus.name:
            existing = Campus.query.filter_by(name=name).first()
            if existing:
                flash('A campus with this name already exists. Please choose a unique name.', 'error')
                return redirect(url_for('main.campus_settings', campus_id=campus.id))
            campus.name = name

        if domain:
            if domain.startswith('@'):
                domain = domain[1:]
            if not current_user.has_verified_domain(domain):
                flash(f'To restrict this campus to @{domain}, you must verify an email ending in @{domain} first.', 'error')
                return redirect(url_for('main.campus_settings', campus_id=campus.id))
            campus.domain = domain
        else:
            campus.domain = None

        campus.description = description

        # Handle file uploads
        upload_folder = os.path.join(current_app.static_folder, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)

        banner_file = request.files.get('banner_image')
        if banner_file and allowed_file(banner_file.filename):
            filename = secure_filename(f"banner_{campus.name}_{banner_file.filename}")
            banner_file.save(os.path.join(upload_folder, filename))
            campus.banner_image = url_for('static', filename=f"uploads/{filename}")

        map_file = request.files.get('map_image')
        if map_file and allowed_file(map_file.filename):
            filename = secure_filename(f"map_{campus.name}_{map_file.filename}")
            map_file.save(os.path.join(upload_folder, filename))
            campus.map_image = url_for('static', filename=f"uploads/{filename}")

        db.session.commit()
        flash('Campus settings updated successfully!', 'success')
        return redirect(url_for('main.campus_settings', campus_id=campus.id))

    # GET request
    moderators = CampusMember.query.filter_by(campus_id=campus.id, role='moderator').all()
    owner_membership = CampusMember.query.filter_by(campus_id=campus.id, role='owner').first()
    return render_template('main/campus_settings.html', campus=campus, moderators=moderators, owner_membership=owner_membership, active_page='campus_settings')


@main_bp.route('/campus/<int:campus_id>/settings/add-moderator', methods=['POST'])
@login_required
def add_moderator(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    if not current_user.is_campus_owner(campus.id):
        flash('Unauthorized action. Only the campus owner can manage roles.', 'error')
        return redirect(url_for('main.dashboard'))

    email = request.form.get('email', '').strip().lower()
    if not email:
        flash('Email address is required.', 'error')
        return redirect(url_for('main.campus_settings', campus_id=campus.id))

    from app.models import User
    user = User.query.filter_by(email=email).first()
    if not user:
        flash(f'No user found with email {email}.', 'error')
        return redirect(url_for('main.campus_settings', campus_id=campus.id))

    member = CampusMember.query.filter_by(user_id=user.id, campus_id=campus.id).first()
    if not member:
        flash(f'{user.name} ({email}) has not joined this campus. They must join the campus first.', 'error')
        return redirect(url_for('main.campus_settings', campus_id=campus.id))

    if member.role == 'owner':
        flash('This user is already the owner.', 'info')
        return redirect(url_for('main.campus_settings', campus_id=campus.id))

    if member.role == 'moderator':
        flash(f'{user.name} is already a moderator.', 'info')
        return redirect(url_for('main.campus_settings', campus_id=campus.id))

    member.role = 'moderator'

    # Notify user
    notif = Notification(
        user_id=user.id,
        title='Promoted to Moderator',
        message=f'You have been promoted to Moderator in {campus.name}!',
        link=url_for('main.dashboard')
    )
    db.session.add(notif)
    db.session.commit()

    flash(f'{user.name} has been successfully added as a moderator.', 'success')
    return redirect(url_for('main.campus_settings', campus_id=campus.id))


@main_bp.route('/campuses/<int:campus_id>/members/<int:user_id>/demote', methods=['POST'])
@login_required
def demote_member(campus_id, user_id):
    # Verify current user is owner of the campus
    owner_membership = CampusMember.query.filter_by(user_id=current_user.id, campus_id=campus_id).first()
    if not owner_membership or owner_membership.role != 'owner':
        flash('Unauthorized action. Only the campus owner can manage roles.', 'error')
        return redirect(url_for('main.dashboard'))

    # Find the target member
    target_membership = CampusMember.query.filter_by(user_id=user_id, campus_id=campus_id).first()
    if not target_membership:
        flash('Member not found in this campus.', 'error')
        return redirect(request.referrer or url_for('main.dashboard'))

    if target_membership.role == 'owner':
        flash('Cannot demote the owner.', 'error')
        return redirect(request.referrer or url_for('main.dashboard'))

    if target_membership.role == 'user':
        flash('This member is already a basic member.', 'info')
        return redirect(request.referrer or url_for('main.dashboard'))

    # Demote
    target_membership.role = 'user'
    
    # Generate Notification
    campus = Campus.query.get(campus_id)
    notif = Notification(
        user_id=user_id,
        title='Role Demoted',
        message=f'You have been demoted to Member in {campus.name}.',
        link=url_for('main.dashboard')
    )
    db.session.add(notif)
    db.session.commit()

    flash(f'{target_membership.user.name} has been demoted to Member.', 'success')
    return redirect(request.referrer or url_for('main.campus_settings', campus_id=campus_id))


@main_bp.route('/campuses/<int:campus_id>/delete', methods=['POST', 'DELETE'])
@login_required
def delete_campus(campus_id):
    # Verify campus exists
    campus = Campus.query.get_or_404(campus_id)

    if campus.creator_id != current_user.id:
        flash('Unauthorized action. Only the campus owner can delete the campus.', 'error')
        return redirect(url_for('main.dashboard'))

    campus_name = campus.name
    
    # Delete campus
    db.session.delete(campus)
    db.session.commit()

    flash(f'Campus "{campus_name}" has been deleted successfully.', 'success')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/notifications', methods=['GET'])
@login_required
def notifications():
    user_notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('main/notifications.html', notifications=user_notifs)


@main_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def read_notification(notification_id):
    notif = Notification.query.get_or_404(notification_id)
    
    if notif.user_id != current_user.id:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('main.dashboard'))
        
    notif.is_read = True
    db.session.commit()
    
    return redirect(url_for('main.notifications'))


@main_bp.route('/notifications/clear', methods=['POST'])
@login_required
def clear_notifications():
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    flash('All notifications cleared.', 'success')
    return redirect(url_for('main.notifications'))


@main_bp.route('/api/notifications/unread-count', methods=['GET'])
@login_required
def api_unread_notifications_count():
    # Calling this endpoint will also trigger check_event_notifications via before_app_request
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})


@main_bp.route('/settings/update-profile', methods=['POST'])
@login_required
def update_profile():
    from app.models import User, UserEmail
    from app.auth.routes import EMAIL_RE

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    
    if not name or not email:
        flash('Display name and email address are required.', 'error')
        return redirect(url_for('main.settings'))
        
    if len(name) < 2:
        flash('Please enter a valid full name.', 'error')
        return redirect(url_for('main.settings'))
        
    if not EMAIL_RE.match(email):
        flash('Please enter a valid email address.', 'error')
        return redirect(url_for('main.settings'))
        
    # Check if login email already in use by another user's primary email
    other_user = User.query.filter(User.id != current_user.id, User.email == email).first()
    if other_user:
        flash('This email address is already in use by another account.', 'error')
        return redirect(url_for('main.settings'))
        
    # Check if login email already in use by anyone's secondary email
    other_secondary = UserEmail.query.filter_by(email=email).first()
    if other_secondary:
        flash('This email address is already in use.', 'error')
        return redirect(url_for('main.settings'))
        
    # Update current user
    current_user.name = name
    current_user.email = email
    db.session.commit()
    
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('main.settings'))


@main_bp.route('/campus/<int:campus_id>/resources')
@login_required
def campus_resources(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    if not _is_member(campus):
        flash('You must join this campus to view its resources.', 'error')
        return redirect(url_for('main.join_campus'))
    resources = Resource.query.filter_by(campus_id=campus.id).all()
    requests = ResourceRequest.query.filter_by(campus_id=campus.id).all()
    posts = []
    for r in resources:
        posts.append(('resource', r, r.uploaded_at))
    for r in requests:
        posts.append(('request', r, r.created_at))
    posts.sort(key=lambda post: post[2], reverse=True)
    return render_template('main/campus_resources.html', campus=campus, posts=posts, active_page='resources')


@main_bp.route('/campus/<int:campus_id>/resources/request', methods=['POST'])
@login_required
def resource_request_create(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    if not _is_member(campus):
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    email = data.get('email', '').strip()
    course_code = data.get('course_code', '').strip().upper()
    chapters = []
    for c in data.get('chapters', []):
        if c.strip():
            chapters.append(c.strip())

    if not re.match(r'^[\w.+\-]+@[\w\-]+(\.[a-zA-Z]{2,}){1,3}$', email):
        return jsonify({'error': 'Invalid email address.'}), 400
    if not course_code:
        return jsonify({'error': 'Course code is required.'}), 400

    if chapters:
        chapters_str = ','.join(chapters)
    else:
        chapters_str = None

    rr = ResourceRequest(
        campus_id=campus_id,
        poster_id=current_user.id,
        email=email,
        course_code=course_code,
        chapters=chapters_str
    )
    db.session.add(rr)
    db.session.commit()

    return jsonify({
        'id': rr.id,
        'email': rr.email,
        'course_code': rr.course_code,
        'chapters': rr.chapters.split(',') if rr.chapters else [],
        'poster_id': rr.poster_id,
        'poster_name': current_user.name,
    }), 201


@main_bp.route('/campus/<int:campus_id>/resources/request/<int:request_id>', methods=['DELETE'])
@login_required
def resource_request_delete(campus_id, request_id):
    rr = ResourceRequest.query.filter_by(id=request_id, campus_id=campus_id).first_or_404()
    if rr.poster_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    db.session.delete(rr)
    db.session.commit()
    return jsonify({'success': True})


@main_bp.route('/campus/<int:campus_id>/resources/upload', methods=['POST'])
@login_required
def resource_create(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    if not _is_member(campus):
        return jsonify({'error': 'Unauthorized'}), 403

    course_code = request.form.get('course_code', '').strip().upper()
    chapters = request.form.get('chapters', '').strip()
    file = request.files.get('file')

    if not course_code:
        return jsonify({'error': 'Course code is required.'}), 400
    if not file or not file.filename:
        return jsonify({'error': 'No file uploaded.'}), 400
    if not allowed_resource(file.filename):
        return jsonify({'error': 'File type not allowed. Use PDF, PPTX, DOCX, DOC, PPT, or XLSX.'}), 400

    original_filename = file.filename
    ext = original_filename.rsplit('.', 1)[1].lower()
    safe = secure_filename(original_filename)
    stored_name = f"{uuid.uuid4().hex}_{safe}"

    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'resources')
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, stored_name))

    if chapters:
        chapters_val = chapters
    else:
        chapters_val = None

    resource = Resource(
        title=original_filename,
        file_url=f"uploads/resources/{stored_name}",
        campus_id=campus_id,
        uploader_id=current_user.id,
        course_code=course_code,
        chapters=chapters_val,
        file_type=ext,
        original_filename=original_filename
    )
    db.session.add(resource)
    db.session.commit()

    return jsonify({
        'id': resource.id,
        'course_code': resource.course_code,
        'chapters': resource.chapters or '',
        'file_type': resource.file_type,
        'original_filename': resource.original_filename,
        'uploader_id': resource.uploader_id,
        'uploader_name': current_user.name,
    }), 201


@main_bp.route('/campus/<int:campus_id>/resources/<int:resource_id>', methods=['DELETE'])
@login_required
def resource_delete(campus_id, resource_id):
    resource = Resource.query.filter_by(id=resource_id, campus_id=campus_id).first_or_404()
    if resource.uploader_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    if resource.file_url:
        file_path = os.path.join(current_app.static_folder, resource.file_url)
        if os.path.exists(file_path):
            os.remove(file_path)
    db.session.delete(resource)
    db.session.commit()
    return jsonify({'success': True})


@main_bp.route('/campus/<int:campus_id>/resources/<int:resource_id>/download')
@login_required
def resource_download(campus_id, resource_id):
    resource = Resource.query.filter_by(id=resource_id, campus_id=campus_id).first_or_404()
    if not resource.file_url:
        flash('File not found.', 'error')
        return redirect(url_for('main.campus_resources', campus_id=campus_id))
    directory = os.path.join(current_app.static_folder, 'uploads', 'resources')
    stored_name = resource.file_url.split('/')[-1]
    return send_from_directory(directory, stored_name, as_attachment=True,
                               download_name=resource.original_filename or stored_name)


@main_bp.route('/campus/<int:campus_id>/market')
@login_required
def campus_market(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    if not _is_member(campus):
        flash('You must join this campus to view its marketplace.', 'error')
        return redirect(url_for('main.join_campus'))
    posts = TutorPost.query.filter_by(campus_id=campus_id).order_by(TutorPost.created_at.desc()).all()
    return render_template('main/campus_market.html', campus=campus, posts=posts, active_page='market')


@main_bp.route('/campus/<int:campus_id>/market/post', methods=['POST'])
@login_required
def market_post_create(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    if not _is_member(campus):
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    role = data.get('role', '').strip()
    courses = []
    for c in data.get('courses', []):
        if c.strip():
            courses.append(c.strip())
    method = data.get('method', '').strip()

    if len(full_name) < 2:
        return jsonify({'error': 'Name must be at least 2 characters.'}), 400
    if not re.match(r'^[\w.+\-]+@[\w\-]+(\.[a-zA-Z]{2,}){1,3}$', email):
        return jsonify({'error': 'Invalid email address.'}), 400
    if role not in ('tutor', 'student'):
        return jsonify({'error': 'Invalid role.'}), 400
    if not courses:
        return jsonify({'error': 'At least one course is required.'}), 400
    if method not in ('online', 'in-person', 'hybrid', 'no-preference'):
        return jsonify({'error': 'Invalid method.'}), 400

    post = TutorPost(
        campus_id=campus_id,
        poster_id=current_user.id,
        full_name=full_name,
        email=email,
        role=role,
        courses=','.join(courses),
        method=method
    )
    db.session.add(post)
    db.session.commit()

    return jsonify({
        'id': post.id,
        'full_name': post.full_name,
        'email': post.email,
        'role': post.role,
        'courses': post.courses.split(','),
        'method': post.method,
        'poster_id': post.poster_id,
        'poster_name': current_user.name
    }), 201


@main_bp.route('/campus/<int:campus_id>/market/post/<int:post_id>', methods=['DELETE'])
@login_required
def market_post_delete(campus_id, post_id):
    post = TutorPost.query.filter_by(id=post_id, campus_id=campus_id).first_or_404()
    if post.poster_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    db.session.delete(post)
    db.session.commit()
    return jsonify({'success': True})


# ── Chat helpers ──────────────────────────────────────────────────────────────

def _campus_member_or_403(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    member = CampusMember.query.filter_by(user_id=current_user.id, campus_id=campus_id).first()
    if not member:
        abort(403)
    return campus, member


# ── Chat routes ───────────────────────────────────────────────────────────────

@main_bp.route('/campus/<int:campus_id>/chat')
@login_required
def chat_browse(campus_id):
    campus, member = _campus_member_or_403(campus_id)
    rooms = ChatRoom.query.filter_by(campus_id=campus_id).all()
    joined_ids = []
    for cm in ChatMember.query.filter_by(user_id=current_user.id).all():
        joined_ids.append(cm.room_id)
    return render_template('main/chat_browse.html', campus=campus, rooms=rooms,
                           joined_ids=joined_ids, member=member, active_page='chat')


@main_bp.route('/campus/<int:campus_id>/chat/create', methods=['POST'])
@login_required
def chat_create(campus_id):
    _campus_member_or_403(campus_id)
    name = (request.json or {}).get('name', '').strip()
    if not name:
        return jsonify({'error': 'Name required'}), 400
    if ChatRoom.query.filter_by(campus_id=campus_id, name=name).first():
        return jsonify({'error': 'A room with that name already exists'}), 400
    room = ChatRoom(campus_id=campus_id, name=name)
    db.session.add(room)
    db.session.commit()
    db.session.add(ChatMember(user_id=current_user.id, room_id=room.id))
    db.session.commit()
    return jsonify({'id': room.id, 'name': room.name}), 201


@main_bp.route('/campus/<int:campus_id>/chat/<int:room_id>/join', methods=['POST'])
@login_required
def chat_join(campus_id, room_id):
    _campus_member_or_403(campus_id)
    ChatRoom.query.filter_by(id=room_id, campus_id=campus_id).first_or_404()
    count = ChatMember.query.filter_by(user_id=current_user.id).count()
    if count >= 14:
        return jsonify({'error': 'You can join at most 14 chat groups.'}), 400
    if ChatMember.query.filter_by(user_id=current_user.id, room_id=room_id).first():
        return jsonify({'ok': True})
    db.session.add(ChatMember(user_id=current_user.id, room_id=room_id))
    db.session.commit()
    return jsonify({'ok': True})


@main_bp.route('/campus/<int:campus_id>/chat/<int:room_id>/delete', methods=['POST'])
@login_required
def chat_delete(campus_id, room_id):
    campus, member = _campus_member_or_403(campus_id)
    if member.role not in ('owner', 'moderator'):
        abort(403)
    room = ChatRoom.query.filter_by(id=room_id, campus_id=campus_id).first_or_404()
    db.session.delete(room)
    db.session.commit()
    return jsonify({'ok': True})


@main_bp.route('/campus/<int:campus_id>/chat/<int:room_id>/leave', methods=['POST'])
@login_required
def chat_leave(campus_id, room_id):
    cm = ChatMember.query.filter_by(user_id=current_user.id, room_id=room_id).first_or_404()
    db.session.delete(cm)
    db.session.commit()
    return jsonify({'ok': True})


@main_bp.route('/campus/<int:campus_id>/chat/<int:room_id>')
@login_required
def chat_room(campus_id, room_id):
    campus, member = _campus_member_or_403(campus_id)
    room = ChatRoom.query.filter_by(id=room_id, campus_id=campus_id).first_or_404()
    cm = ChatMember.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    if not cm:
        return redirect(url_for('main.chat_browse', campus_id=campus_id))
    cm.last_read_at = datetime.utcnow()
    db.session.commit()
    msgs = ChatMessage.query.filter_by(room_id=room_id).order_by(ChatMessage.sent_at.asc()).all()
    return render_template('main/chat_room.html', campus=campus, room=room,
                           messages=msgs, member=member, active_page='chat')


@main_bp.route('/campus/<int:campus_id>/chat/<int:room_id>/send', methods=['POST'])
@login_required
def chat_send(campus_id, room_id):
    cm = ChatMember.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    if not cm:
        return jsonify({'error': 'Not a member'}), 403
    body = (request.json or {}).get('body', '').strip()
    if not body or len(body) > 2000:
        return jsonify({'error': 'Invalid message'}), 400
    msg = ChatMessage(room_id=room_id, sender_id=current_user.id, body=body)
    db.session.add(msg)
    cm.last_read_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'id': msg.id, 'body': msg.body, 'sender': current_user.name})


@main_bp.route('/campus/<int:campus_id>/chat/<int:room_id>/poll')
@login_required
def chat_poll(campus_id, room_id):
    cm = ChatMember.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    if not cm:
        return jsonify({'error': 'Not a member'}), 403
    after = request.args.get('after', 0, type=int)
    msgs = ChatMessage.query.filter(
        ChatMessage.room_id == room_id,
        ChatMessage.id > after
    ).order_by(ChatMessage.sent_at.asc()).all()
    if msgs:
        cm.last_read_at = datetime.utcnow()
        db.session.commit()
    result = []
    for m in msgs:
        result.append({
            'id': m.id,
            'body': m.body,
            'sender': m.sender.name,
            'mine': m.sender_id == current_user.id
        })
    return jsonify(result)


# ── Hook: Event Start Notifications ───────────────────────────────────────────

@main_bp.before_app_request
def check_event_notifications():
    if current_user.is_authenticated:
        now = datetime.utcnow()
        all_participations = EventParticipation.query.filter_by(
            user_id=current_user.id,
            want_notification=True,
            notification_sent=False
        ).all()
        due_participations = []
        for p in all_participations:
            if p.event.date <= now:
                due_participations.append(p)

        if due_participations:
            for p in due_participations:
                notif = Notification(
                    user_id=current_user.id,
                    title=f"📅 Event Started: {p.event.title}",
                    message=f"The event '{p.event.title}' has started! Click to explore it on the map.",
                    is_read=False,
                    link=url_for('map.campus_map', campus_id=p.event.campus_id, view='events')
                )
                db.session.add(notif)
                p.notification_sent = True
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Failed to save auto event notification: {e}")

