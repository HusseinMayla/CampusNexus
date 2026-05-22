import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Campus

main_bp = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route('/')
@main_bp.route('/index')
@login_required
def index():
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    campuses = Campus.query.all()
    return render_template('main/dashboard.html', campuses=campuses)

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
            map_image=url_for('static', filename=map_filename) if map_filename else None
        )
        db.session.add(new_campus)
        db.session.commit()
        flash('Campus created successfully!')
        return redirect(url_for('main.dashboard'))

    return render_template('main/create_campus.html')

@main_bp.route('/join-campus')
def join_campus():
    return render_template('main/join_campus.html')

@main_bp.route('/settings')
def settings():
    return render_template('main/settings.html')
