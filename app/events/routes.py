from flask import Blueprint

events_bp = Blueprint('events', __name__, url_prefix='/events')

@events_bp.route('/')
def list_events():
    return "Events List"
