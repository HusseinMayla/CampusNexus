import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Campus, CampusMember, CampusReport, Notification, Resource, MarketListing
from sqlalchemy import func

main_bp = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route('/')
@main_bp.route('/index')
@login_required
def index():
    return render_template('index.html', active_page='home')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    created  = Campus.query.filter_by(creator_id=current_user.id).all()
    memberships = CampusMember.query.filter_by(user_id=current_user.id).all()
    joined   = [m.campus for m in memberships]
    campuses = created + [c for c in joined if c not in created]
    return render_template('main/dashboard.html', campuses=campuses, created_ids={c.id for c in created})

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

        new_campus = Campus(
            name=name,
            description=description,
            domain=domain if domain else None,
            banner_image=url_for('static', filename=banner_filename) if banner_filename else None,
            map_image=url_for('static', filename=map_filename) if map_filename else None,
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
    joined_roles = {m.campus_id: m.role for m in joined_memberships}
    
    campus_list = []
    for campus, count in campuses_with_counts:
        role = joined_roles.get(campus.id)
        campus_list.append({
            'campus': campus,
            'member_count': count,
            'is_joined': campus.id in joined_roles or campus.creator_id == current_user.id,
            'role': role or ('owner' if campus.creator_id == current_user.id else None)
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


@main_bp.route('/explore')
@login_required
def explore():
    # Sort campuses by popularity (member count)
    campuses_with_counts = db.session.query(
        Campus, 
        func.count(CampusMember.id).label('member_count')
    ).outerjoin(CampusMember)\
     .group_by(Campus.id)\
     .order_by(func.count(CampusMember.id).desc())\
     .all()
     
    # Convert list of tuples (Campus, member_count) into a clean context structure
    # and check if the current user has already joined
    joined_ids = {m.campus_id for m in CampusMember.query.filter_by(user_id=current_user.id).all()}
    
    explore_list = []
    for campus, member_count in campuses_with_counts:
        explore_list.append({
            'campus': campus,
            'member_count': member_count,
            'is_joined': campus.id in joined_ids or campus.creator_id == current_user.id
        })

    return render_template('main/explore.html', campuses=explore_list)


@main_bp.route('/campuses/<int:campus_id>/report', methods=['POST'])
@login_required
def report_campus(campus_id):
    reason = request.form.get('reason', '').strip()
    
    # Check if campus exists
    campus = Campus.query.get_or_404(campus_id)
    
    # Cannot report own campus
    if campus.creator_id == current_user.id:
        flash('You cannot report your own campus.', 'error')
        return redirect(url_for('main.dashboard'))
        
    # Check if already reported
    already = CampusReport.query.filter_by(campus_id=campus_id, reporter_id=current_user.id).first()
    if already:
        flash('You have already reported this campus.', 'error')
        return redirect(url_for('main.dashboard'))
        
    # Create the report
    report = CampusReport(campus_id=campus_id, reporter_id=current_user.id, reason=reason)
    db.session.add(report)
    db.session.commit()
    
    flash(f'Thank you for reporting {campus.name}. Our administrators will review it.', 'success')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/campuses/<int:campus_id>/members/<int:user_id>/promote', methods=['POST'])
@login_required
def promote_member(campus_id, user_id):
    # Verify current user is owner of the campus
    owner_membership = CampusMember.query.filter_by(user_id=current_user.id, campus_id=campus_id).first()
    if not owner_membership or owner_membership.role != 'owner':
        flash('Unauthorized action. Only the campus owner can manage roles.', 'error')
        return redirect(url_for('main.dashboard'))

    # Find the target member
    target_membership = CampusMember.query.filter_by(user_id=user_id, campus_id=campus_id).first()
    if not target_membership:
        flash('Member not found in this campus.', 'error')
        return redirect(url_for('main.dashboard'))

    if target_membership.role == 'owner':
        flash('Cannot promote the owner.', 'error')
        return redirect(url_for('main.dashboard'))

    if target_membership.role == 'admin':
        flash('This member is already an admin.', 'info')
        return redirect(url_for('main.dashboard'))

    # Promote
    target_membership.role = 'admin'
    
    # Generate Notification
    campus = Campus.query.get(campus_id)
    notif = Notification(
        user_id=user_id,
        title='Promoted to Admin',
        message=f'You have been promoted to Admin in {campus.name}!',
        link=url_for('main.dashboard')
    )
    db.session.add(notif)
    db.session.commit()

    flash(f'{target_membership.user.name} has been promoted to Admin.', 'success')
    return redirect(url_for('main.dashboard'))


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
        return redirect(url_for('main.dashboard'))

    if target_membership.role == 'owner':
        flash('Cannot demote the owner.', 'error')
        return redirect(url_for('main.dashboard'))

    if target_membership.role == 'user':
        flash('This member is already a basic member.', 'info')
        return redirect(url_for('main.dashboard'))

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
    return redirect(url_for('main.dashboard'))


@main_bp.route('/campuses/<int:campus_id>/delete', methods=['POST', 'DELETE'])
@login_required
def delete_campus(campus_id):
    # Verify campus exists
    campus = Campus.query.get_or_404(campus_id)

    # Verify current user is owner of the campus
    owner_membership = CampusMember.query.filter_by(user_id=current_user.id, campus_id=campus_id).first()
    if not owner_membership or owner_membership.role != 'owner':
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


@main_bp.route('/campus/<int:campus_id>/resources', methods=['GET', 'POST'])
@login_required
def campus_resources(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    is_member = CampusMember.query.filter_by(user_id=current_user.id, campus_id=campus.id).first() is not None or campus.creator_id == current_user.id
    if not is_member:
        flash('You must join this campus to view its resources.', 'error')
        return redirect(url_for('main.join_campus'))
        
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        file_url = request.form.get('file_url', '').strip()
        
        if not title:
            flash('Title is required.', 'error')
            return redirect(url_for('main.campus_resources', campus_id=campus_id))
            
        new_resource = Resource(
            title=title,
            description=description,
            file_url=file_url if file_url else None,
            campus_id=campus.id,
            uploader_id=current_user.id
        )
        db.session.add(new_resource)
        db.session.commit()
        flash('Resource uploaded successfully!', 'success')
        return redirect(url_for('main.campus_resources', campus_id=campus_id))
        
    # Get all resources for this campus
    resources = Resource.query.filter_by(campus_id=campus.id).order_by(Resource.uploaded_at.desc()).all()
    return render_template('main/campus_resources.html', campus=campus, resources=resources, active_page='resources')


@main_bp.route('/campus/<int:campus_id>/market', methods=['GET', 'POST'])
@login_required
def campus_market(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    is_member = CampusMember.query.filter_by(user_id=current_user.id, campus_id=campus.id).first() is not None or campus.creator_id == current_user.id
    if not is_member:
        flash('You must join this campus to view its marketplace.', 'error')
        return redirect(url_for('main.join_campus'))
        
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        price_str = request.form.get('price', '').strip()
        contact = request.form.get('contact', '').strip()
        image_url = request.form.get('image_url', '').strip()
        
        if not title or not price_str or not contact:
            flash('Title, Price, and Contact information are required.', 'error')
            return redirect(url_for('main.campus_market', campus_id=campus_id))
            
        try:
            price = float(price_str)
        except ValueError:
            flash('Please enter a valid price.', 'error')
            return redirect(url_for('main.campus_market', campus_id=campus_id))
            
        new_listing = MarketListing(
            title=title,
            description=description,
            price=price,
            contact=contact,
            image_url=image_url if image_url else None,
            campus_id=campus.id,
            seller_id=current_user.id
        )
        db.session.add(new_listing)
        db.session.commit()
        flash('Item listed successfully!', 'success')
        return redirect(url_for('main.campus_market', campus_id=campus_id))
        
    # Get all market listings for this campus
    listings = MarketListing.query.filter_by(campus_id=campus.id).order_by(MarketListing.created_at.desc()).all()
    return render_template('main/campus_market.html', campus=campus, listings=listings, active_page='market')

