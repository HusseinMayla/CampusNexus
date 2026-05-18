from flask import Blueprint, render_template, redirect, url_for, flash
from app.extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login')
def login():
    return "Login Page"

@auth_bp.route('/register')
def register():
    return "Register Page"

@auth_bp.route('/logout')
def logout():
    return "Logout"
