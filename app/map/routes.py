from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Campus, Club, Office, Event
from datetime import datetime

map_bp = Blueprint('map', __name__)


# ── Page ──────────────────────────────────────────────────────────────────────

@map_bp.route('/campus/<int:campus_id>/map')
@login_required
def campus_map(campus_id):
    campus   = Campus.query.get_or_404(campus_id)
    is_admin = (campus.creator_id == current_user.id)
    return render_template('main/campus_map.html', campus=campus, is_admin=is_admin)


# ── API: fetch all pins ───────────────────────────────────────────────────────

@map_bp.route('/api/map-data/<int:campus_id>')
@login_required
def map_data(campus_id):
    now  = datetime.utcnow()
    pins = []

    for c in Club.query.filter_by(campus_id=campus_id).all():
        if c.lat and c.lng:
            pins.append({
                'id': c.id, 'type': 'club',
                'name': c.name, 'description': c.description or '',
                'lat': c.lat, 'lng': c.lng
            })

    for o in Office.query.filter_by(campus_id=campus_id).all():
        if o.lat and o.lng:
            pins.append({
                'id': o.id, 'type': 'office',
                'name': o.name, 'description': o.description or '',
                'lat': o.lat, 'lng': o.lng
            })

    for e in Event.query.join(Club).filter(
        Club.campus_id == campus_id,
        Event.date >= now
    ).all():
        if e.lat and e.lng:
            pins.append({
                'id': e.id, 'type': 'event',
                'name': e.title, 'description': e.description or '',
                'lat': e.lat, 'lng': e.lng,
                'date': e.date.isoformat()
            })

    return jsonify(pins)


# ── API: add pin ──────────────────────────────────────────────────────────────

@map_bp.route('/api/pin/add', methods=['POST'])
@login_required
def add_pin():
    data      = request.get_json()
    campus_id = data.get('campus_id')
    campus    = Campus.query.get(campus_id)

    if not campus or campus.creator_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    pin_type = data.get('type')
    name     = data.get('name', '').strip()
    desc     = data.get('description', '').strip()
    lat      = data.get('lat')
    lng      = data.get('lng')

    if not name or not lat or not lng:
        return jsonify({'error': 'Missing fields'}), 400

    if pin_type == 'club':
        obj = Club(name=name, description=desc, campus_id=campus_id, lat=lat, lng=lng)
        db.session.add(obj)
        db.session.commit()
        return jsonify({'id': obj.id, 'type': 'club', 'name': name,
                        'description': desc, 'lat': lat, 'lng': lng})

    elif pin_type == 'office':
        obj = Office(name=name, description=desc, campus_id=campus_id, lat=lat, lng=lng)
        db.session.add(obj)
        db.session.commit()
        return jsonify({'id': obj.id, 'type': 'office', 'name': name,
                        'description': desc, 'lat': lat, 'lng': lng})

    elif pin_type == 'event':
        date_str = data.get('date')
        if not date_str:
            return jsonify({'error': 'Event date required'}), 400
        event_date = datetime.fromisoformat(date_str)

        club = Club.query.filter_by(campus_id=campus_id).first()
        if not club:
            return jsonify({'error': 'Add a club first before adding events'}), 400

        obj = Event(title=name, description=desc, club_id=club.id,
                    date=event_date, lat=lat, lng=lng)
        db.session.add(obj)
        db.session.commit()
        return jsonify({'id': obj.id, 'type': 'event', 'name': name,
                        'description': desc, 'lat': lat, 'lng': lng,
                        'date': event_date.isoformat()})

    return jsonify({'error': 'Unknown pin type'}), 400


# ── API: delete pin ───────────────────────────────────────────────────────────

@map_bp.route('/api/pin/delete/<pin_type>/<int:pin_id>', methods=['DELETE'])
@login_required
def delete_pin(pin_type, pin_id):
    model_map = {'club': Club, 'office': Office, 'event': Event}
    Model = model_map.get(pin_type)
    if not Model:
        return jsonify({'error': 'Unknown type'}), 400

    obj = Model.query.get_or_404(pin_id)

    campus_id = obj.campus_id if hasattr(obj, 'campus_id') else obj.club.campus_id
    campus    = Campus.query.get(campus_id)
    if not campus or campus.creator_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(obj)
    db.session.commit()
    return jsonify({'success': True})


# ── API: set campus center ────────────────────────────────────────────────────

@map_bp.route('/api/campus/set-center', methods=['POST'])
@login_required
def set_center():
    data   = request.get_json()
    campus = Campus.query.get(data.get('campus_id'))
    if not campus or campus.creator_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    campus.center_lat = data.get('lat')
    campus.center_lng = data.get('lng')
    db.session.commit()
    return jsonify({'success': True})
