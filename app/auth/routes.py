import re
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Message
from app.extensions import db, mail
from app.models import User, UserEmail
import bcrypt

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.(edu(\.[a-z]{2,})?|ac\.[a-z]{2,})$', re.IGNORECASE)


def send_verification_email(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = s.dumps(email, salt='email-verify')
    link = url_for('auth.verify_token', token=token, _external=True)
    sender = current_app.config['MAIL_USERNAME']
    current_app.logger.error(f'DEBUG sender={sender}')
    msg = Message('Verify your Agora account', sender=sender, recipients=[email])
    msg.body = f'Hi! Click the link below to verify your email address:\n\n{link}\n\nThis link expires in 1 hour.'
    mail.send(msg)


def send_secondary_verification_email(user_email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = s.dumps(user_email.id, salt='secondary-email-verify')
    link = url_for('auth.verify_secondary_token', token=token, _external=True)
    sender = current_app.config['MAIL_USERNAME']
    current_app.logger.error(f'DEBUG sender={sender}')
    msg = Message('Verify your secondary email address', sender=sender, recipients=[user_email.email])
    msg.body = f'Hi! Click the link below to verify your secondary email address:\n\n{link}\n\nThis link expires in 1 hour.'
    mail.send(msg)


@auth_bp.route('/')
def page():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('auth/login.html')


@auth_bp.route('/login', methods=['POST'])
def login():
    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    next_url = request.form.get('next', '').strip()

    if not email or not password:
        flash('All fields are required.', 'error')
        return redirect(url_for('auth.page'))

    if not EMAIL_RE.match(email):
        flash('Please use a university email address (.edu or .ac.xx).', 'error')
        return redirect(url_for('auth.page'))

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        flash('Invalid email or password.', 'error')
        return redirect(url_for('auth.page'))

    if not user.is_verified:
        flash('Please verify your email before logging in. Check your inbox.', 'error')
        return redirect(url_for('auth.page'))

    login_user(user)
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect(url_for('main.dashboard'))


@auth_bp.route('/register', methods=['POST'])
def register():
    name     = request.form.get('name', '').strip()
    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    signup_url = url_for('auth.page') + '?tab=signup'

    if not name or not email or not password:
        flash('All fields are required.', 'error')
        return redirect(signup_url)

    if len(name) < 2:
        flash('Please enter your full name.', 'error')
        return redirect(signup_url)

    if not EMAIL_RE.match(email):
        flash('Please use a university email address (.edu or .ac.xx).', 'error')
        return redirect(signup_url)

    if len(password) < 8:
        flash('Password must be at least 8 characters.', 'error')
        return redirect(signup_url)

    # Check if this email exists as a verified primary or verified secondary email
    verified_primary = User.query.filter_by(email=email, is_verified=True).first()
    verified_secondary = UserEmail.query.filter_by(email=email, is_verified=True).first()

    if verified_primary or verified_secondary:
        flash('An account with this email already exists.', 'error')
        return redirect(signup_url)

    # If it exists as an unverified primary email, resend the verification email
    unverified_primary = User.query.filter_by(email=email, is_verified=False).first()
    if unverified_primary:
        try:
            send_verification_email(email)
            flash('This email is already registered but unverified. A new verification link has been sent.', 'success')
        except Exception as e:
            flash(f'Mail error: {e}', 'error')
        return redirect(url_for('auth.page'))

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user   = User(name=name, email=email, password_hash=hashed, is_verified=False)
    db.session.add(user)
    db.session.commit()
    try:
        send_verification_email(email)
        flash(f'Account created! Check {email} for a verification link.', 'success')
    except Exception as e:
        current_app.logger.error(f'Mail error: {e}')
        flash(f'Mail error: {e}', 'error')
    return redirect(url_for('auth.page'))


@auth_bp.route('/verify/<token>')
def verify_token(token):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='email-verify', max_age=3600)
    except SignatureExpired:
        flash('Verification link has expired. Please sign up again.', 'error')
        return redirect(url_for('auth.page'))
    except BadSignature:
        flash('Invalid verification link.', 'error')
        return redirect(url_for('auth.page'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Account not found.', 'error')
        return redirect(url_for('auth.page'))

    user.is_verified = True
    db.session.commit()
    login_user(user)
    flash(f'Email verified! Welcome to Agora, {user.name}!', 'success')
    return redirect(url_for('main.dashboard'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.page'))


@auth_bp.route('/emails', methods=['POST'])
@login_required
def add_email():
    email = request.form.get('email', '').strip().lower()
    
    if not email:
        flash('Email address is required.', 'error')
        return redirect(url_for('main.settings'))
        
    if not EMAIL_RE.match(email):
        flash('Please use a university email address (.edu or .ac.xx).', 'error')
        return redirect(url_for('main.settings'))
        
    # Validation: No email can have more than one user (global uniqueness)
    # 1. Check primary emails
    if User.query.filter_by(email=email).first():
        flash('This email address is already in use by another account.', 'error')
        return redirect(url_for('main.settings'))
        
    # 2. Check secondary emails
    if UserEmail.query.filter_by(email=email).first():
        flash('This email address is already in use.', 'error')
        return redirect(url_for('main.settings'))
        
    # Create the new secondary email
    is_auto_verified = email.split('@')[0].lower() in ['admin', 'it']
    new_email = UserEmail(user_id=current_user.id, email=email, is_verified=is_auto_verified)
    db.session.add(new_email)
    db.session.commit()
    
    if is_auto_verified:
        flash(f'Added and auto-verified administrator email: {email}', 'success')
    else:
        try:
            send_secondary_verification_email(new_email)
            flash(f'Added {email} to your account. A verification link has been sent. Please check your inbox.', 'success')
        except Exception as e:
            current_app.logger.error(f'Mail error: {e}')
            flash(f'Added {email} to your account, but failed to send verification email: {e}', 'error')
    return redirect(url_for('main.settings'))


@auth_bp.route('/emails/<int:email_id>/verify', methods=['POST'])
@login_required
def verify_email(email_id):
    user_email = UserEmail.query.get_or_404(email_id)
    
    # Security check: Ensure it belongs to the current user
    if user_email.user_id != current_user.id:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('main.settings'))
        
    try:
        send_secondary_verification_email(user_email)
        flash(f'A verification link has been sent to {user_email.email}. Please check your inbox.', 'success')
    except Exception as e:
        current_app.logger.error(f'Mail error: {e}')
        flash(f'Mail error: {e}', 'error')
        
    return redirect(url_for('main.settings'))


@auth_bp.route('/verify-secondary/<token>')
def verify_secondary_token(token):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email_id = s.loads(token, salt='secondary-email-verify', max_age=3600)
    except SignatureExpired:
        flash('Verification link has expired. Please request a new link from Settings.', 'error')
        if current_user.is_authenticated:
            return redirect(url_for('main.settings'))
        return redirect(url_for('auth.page'))
    except BadSignature:
        flash('Invalid verification link.', 'error')
        if current_user.is_authenticated:
            return redirect(url_for('main.settings'))
        return redirect(url_for('auth.page'))

    user_email = UserEmail.query.get(email_id)
    if not user_email:
        flash('Email record not found.', 'error')
        if current_user.is_authenticated:
            return redirect(url_for('main.settings'))
        return redirect(url_for('auth.page'))

    user_email.is_verified = True
    db.session.commit()
    
    flash(f'Secondary email {user_email.email} has been verified successfully!', 'success')
    if current_user.is_authenticated:
        return redirect(url_for('main.settings'))
    return redirect(url_for('auth.page'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            flash('Email address is required.', 'error')
            return redirect(url_for('auth.forgot_password_request'))
            
        if not EMAIL_RE.match(email):
            flash('Please enter a valid university email address.', 'error')
            return redirect(url_for('auth.forgot_password_request'))

        # Look up user by primary email
        user = User.query.filter_by(email=email).first()
        
        # If not found, look up by verified secondary email
        if not user:
            user_email = UserEmail.query.filter_by(email=email, is_verified=True).first()
            if user_email:
                user = user_email.user
                
        if user:
            # Generate timed reset token
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = s.dumps(user.id, salt='password-reset')
            link = url_for('auth.reset_password', token=token, _external=True)
            
            # Send the reset email
            sender = current_app.config['MAIL_USERNAME']
            msg = Message('Reset your Agora password', sender=sender, recipients=[email])
            msg.body = f'Hi {user.name}!\n\nClick the link below to reset your password:\n\n{link}\n\nThis link expires in 1 hour.'
            try:
                mail.send(msg)
            except Exception as e:
                current_app.logger.error(f'Mail error during forgot password: {e}')
                
        # Generic success message for privacy/security
        flash('If this email is registered, a password reset link has been sent. Please check your inbox.', 'success')
        return redirect(url_for('auth.page'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token, salt='password-reset', max_age=3600)
    except SignatureExpired:
        flash('The password reset link has expired.', 'error')
        return redirect(url_for('auth.forgot_password_request'))
    except BadSignature:
        flash('Invalid password reset link.', 'error')
        return redirect(url_for('auth.forgot_password_request'))

    user = User.query.get(user_id)
    if not user:
        flash('User account not found.', 'error')
        return redirect(url_for('auth.forgot_password_request'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not password or not confirm_password:
            flash('All fields are required.', 'error')
            return redirect(url_for('auth.reset_password', token=token))

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return redirect(url_for('auth.reset_password', token=token))

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.reset_password', token=token))

        # Update user's password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user.password_hash = hashed
        db.session.commit()

        flash('Your password has been reset successfully! You can now sign in with your new password.', 'success')
        return redirect(url_for('auth.page'))

    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/emails/<int:email_id>/delete', methods=['POST', 'DELETE'])
@login_required
def delete_email(email_id):
    user_email = UserEmail.query.get_or_404(email_id)
    
    # Security check: Ensure it belongs to the current user
    if user_email.user_id != current_user.id:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('main.settings'))
        
    email_str = user_email.email
    db.session.delete(user_email)
    db.session.commit()
    
    flash(f'Email {email_str} has been removed.', 'success')
    return redirect(url_for('main.settings'))


@auth_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    # 1. Campus Ownership Safety Check
    from app.models import Campus
    owned_campuses = Campus.query.filter_by(creator_id=current_user.id).all()
    if owned_campuses:
        campus_names = ", ".join([f'"{c.name}"' for c in owned_campuses])
        flash(f"Cannot delete account. You are the owner of the following campus(es): {campus_names}. You must delete them first.", "error")
        return redirect(url_for('main.settings'))

    # 2. Cleanup physical file uploads for user resources
    for resource in current_user.resources:
        if resource.file_url:
            from flask import current_app
            import os
            file_path = os.path.join(current_app.static_folder, resource.file_url)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

    # 3. Perform logout and user deletion (dependent records will be cascade deleted)
    user = current_user._get_current_object()
    logout_user()
    db.session.delete(user)
    db.session.commit()

    flash("Your account and all associated data have been permanently deleted.", "success")
    return redirect(url_for('auth.page'))

