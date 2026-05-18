from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
def index():
    return render_template('index.html')

@main_bp.route('/test')
def test_route():
    return "App is running! If you see this, the basic Flask setup is working."

@main_bp.route('/dashboard')
def dashboard():
    return "Dashboard Page"
