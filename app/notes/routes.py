from flask import Blueprint

notes_bp = Blueprint('notes', __name__, url_prefix='/notes')

@notes_bp.route('/')
def list_notes():
    return "Notes List"
