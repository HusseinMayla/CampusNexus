import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Campus, CampusMember

main_bp = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route('/')
@main_bp.route('/index')
@login_required
def index():
    campus = Campus.query.filter_by(creator_id=current_user.id).first()
    return render_template('index.html', campus=campus)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    created  = Campus.query.filter_by(creator_id=current_user.id).all()
    memberships = CampusMember.query.filter_by(user_id=current_user.id).all()
    joined   = [m.campus for m in memberships]
    campuses = created + [c for c in joined if c not in created]
    return render_template('main/dashboard.html', campuses=campuses, created_ids={c.id for c in created})

@main_bp.route('/create-campus', methods=['GET', 'POST'])
def create_campus():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Campus name is required!')
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
            banner_image=url_for('static', filename=banner_filename) if banner_filename else None,
            map_image=url_for('static', filename=map_filename) if map_filename else None,
            creator_id=current_user.id
        )
        db.session.add(new_campus)
        db.session.commit()
        flash('Campus created successfully!')
        return redirect(url_for('main.dashboard'))

    return render_template('main/create_campus.html')

@main_bp.route('/join-campus', methods=['GET', 'POST'])
@login_required
def join_campus():
    if request.method == 'POST':
        code   = request.form.get('code', '').strip()
        campus = Campus.query.filter_by(invite_code=code).first()

        if not campus:
            flash('Invalid invitation code.')
            return redirect(url_for('main.join_campus'))

        if campus.creator_id == current_user.id:
            flash('You are already the admin of this campus.')
            return redirect(url_for('main.join_campus'))

        already = CampusMember.query.filter_by(
            user_id=current_user.id, campus_id=campus.id
        ).first()
        if already:
            flash('You have already joined this campus.')
            return redirect(url_for('main.dashboard'))

        db.session.add(CampusMember(user_id=current_user.id, campus_id=campus.id))
        db.session.commit()
        flash(f'You joined {campus.name}!')
        return redirect(url_for('main.dashboard'))

    return render_template('main/join_campus.html')

@main_bp.route('/settings')
def settings():
    return render_template('main/settings.html')
