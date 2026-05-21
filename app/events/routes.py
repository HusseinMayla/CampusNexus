from flask import Blueprint, render_template

events_bp = Blueprint('events', __name__, url_prefix='/events')

@events_bp.route('/')
def list_events():
    # Placeholder events
    events = [
        {'title': 'Campus Orientation', 'date': '2024-06-01', 'location': 'Main Hall'},
        {'title': 'Tech Workshop', 'date': '2024-06-05', 'location': 'Lab 204'},
        {'title': 'Sports Day', 'date': '2024-06-10', 'location': 'University Stadium'}
    ]
    return render_template('events/list_events.html', events=events)
