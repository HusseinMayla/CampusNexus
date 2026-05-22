import re
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User
import bcrypt

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


@auth_bp.route('/')
def page():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('auth/login.html')


@auth_bp.route('/login', methods=['POST'])
def login():
    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    if not email or not password:
        flash('All fields are required.', 'error')
        return redirect(url_for('auth.page'))

    if not EMAIL_RE.match(email):
        flash('Please enter a valid email address.', 'error')
        return redirect(url_for('auth.page'))

    if len(password) < 8:
        flash('Password must be at least 8 characters.', 'error')
        return redirect(url_for('auth.page'))

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        flash('Invalid email or password.', 'error')
        return redirect(url_for('auth.page'))

    login_user(user)
    return redirect(url_for('main.dashboard'))


@auth_bp.route('/register', methods=['POST'])
def register():
    name     = request.form.get('name', '').strip()
    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    if not name or not email or not password:
        flash('All fields are required.', 'error')
        return redirect(url_for('auth.page'))

    if len(name) < 2:
        flash('Please enter your full name.', 'error')
        return redirect(url_for('auth.page'))

    if not EMAIL_RE.match(email):
        flash('Please enter a valid email address.', 'error')
        return redirect(url_for('auth.page'))

    if len(password) < 8:
        flash('Password must be at least 8 characters.', 'error')
        return redirect(url_for('auth.page'))

    if User.query.filter_by(email=email).first():
        flash('An account with this email already exists.', 'error')
        return redirect(url_for('auth.page'))

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user   = User(name=name, email=email, password_hash=hashed)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    flash(f'Welcome to LearnHive, {name}!', 'success')
    return redirect(url_for('main.dashboard'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.page'))
