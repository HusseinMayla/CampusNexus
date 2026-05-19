from flask import Blueprint, render_template, redirect, url_for, flash
from app.extensions import db
from app.auth.forms import LoginForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        return redirect(url_for('main.index'))
    return render_template('auth/login.html', title='Sign In', form=form)

@auth_bp.route('/register')
def register():
    return "Register Page"

@auth_bp.route('/logout')
def logout():
    return "Logout"
