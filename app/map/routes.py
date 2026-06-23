from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Campus, Club, Office, Event, CampusMember, EventParticipation, EventCreationLog
from datetime import datetime, timedelta, timezone

def parse_utc(dt_str):
    if not dt_str:
        return None
    # Convert 'Z' to '+00:00' for compatible ISO parsing
    if dt_str.endswith('Z'):
        dt_str = dt_str[:-1] + '+00:00'
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

map_bp = Blueprint('map', __name__)


def _is_admin(campus):
    membership = CampusMember.query.filter_by(user_id=current_user.id, campus_id=campus.id).first()
    return campus.creator_id == current_user.id or (membership and membership.role in ('moderator', 'owner'))


# ── Page ──────────────────────────────────────────────────────────────────────

@map_bp.route('/campus/<int:campus_id>/map')
@login_required
def campus_map(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    is_admin = _is_admin(campus)
    view = request.args.get('view')
    active_page = 'events' if view == 'events' else 'map'
    return render_template('main/campus_map.html', campus=campus, is_admin=is_admin, active_page=active_page)


@map_bp.route('/campus/<int:campus_id>/add-club', methods=['POST'])
@login_required
def add_club(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    if not _is_admin(campus):
        flash('Unauthorized action.', 'error')
        return redirect(url_for('map.campus_map', campus_id=campus_id))

    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('Club name is required.', 'error')
        return redirect(url_for('map.campus_map', campus_id=campus_id))
        
    club = Club(name=name, description=description, campus_id=campus.id)
    db.session.add(club)
    db.session.commit()
    flash(f'Club "{name}" added successfully!', 'success')
    return redirect(url_for('map.campus_map', campus_id=campus_id))


@map_bp.route('/campus/<int:campus_id>/add-office', methods=['POST'])
@login_required
def add_office(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    if not _is_admin(campus):
        flash('Unauthorized action.', 'error')
        return redirect(url_for('map.campus_map', campus_id=campus_id))

    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('Office name is required.', 'error')
        return redirect(url_for('map.campus_map', campus_id=campus_id))
        
    office = Office(name=name, description=description, campus_id=campus.id)
    db.session.add(office)
    db.session.commit()
    flash(f'Office "{name}" added successfully!', 'success')
    return redirect(url_for('map.campus_map', campus_id=campus_id))


@map_bp.route('/campus/<int:campus_id>/delete-club/<int:club_id>', methods=['POST'])
@login_required
def delete_club(campus_id, club_id):
    campus = Campus.query.get_or_404(campus_id)
    if not _is_admin(campus):
        flash('Unauthorized action.', 'error')
        return redirect(url_for('map.campus_map', campus_id=campus_id))

    club = Club.query.get_or_404(club_id)
    if club.campus_id != campus.id:
        flash('Invalid action.', 'error')
        return redirect(url_for('map.campus_map', campus_id=campus_id))
        
    db.session.delete(club)
    db.session.commit()
    flash(f'Club "{club.name}" deleted successfully.', 'success')
    return redirect(url_for('map.campus_map', campus_id=campus_id))


@map_bp.route('/campus/<int:campus_id>/delete-office/<int:office_id>', methods=['POST'])
@login_required
def delete_office(campus_id, office_id):
    campus = Campus.query.get_or_404(campus_id)
    if not _is_admin(campus):
        flash('Unauthorized action.', 'error')
        return redirect(url_for('map.campus_map', campus_id=campus_id))

    office = Office.query.get_or_404(office_id)
    if office.campus_id != campus.id:
        flash('Invalid action.', 'error')
        return redirect(url_for('map.campus_map', campus_id=campus_id))
        
    db.session.delete(office)
    db.session.commit()
    flash(f'Office "{office.name}" deleted successfully.', 'success')
    return redirect(url_for('map.campus_map', campus_id=campus_id))


# ── API: fetch all pins ───────────────────────────────────────────────────────

@map_bp.route('/api/map-data/<int:campus_id>')
@login_required
def map_data(campus_id):
    pins = []

    for c in Club.query.filter_by(campus_id=campus_id).all():
        if c.lat is not None and c.lng is not None:
            pins.append({
                'id': c.id, 'type': 'club',
                'name': c.name, 'description': c.description or '',
                'lat': c.lat, 'lng': c.lng
            })

    for o in Office.query.filter_by(campus_id=campus_id).all():
        if o.lat is not None and o.lng is not None:
            pins.append({
                'id': o.id, 'type': 'office',
                'name': o.name, 'description': o.description or '',
                'lat': o.lat, 'lng': o.lng
            })

    # Fetch events directly for this campus (excluding those ended for more than 1 hour)
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    for e in Event.query.filter(Event.campus_id == campus_id, Event.end_date >= one_hour_ago).all():
        if e.lat is not None and e.lng is not None:
            part_count = EventParticipation.query.filter_by(event_id=e.id, is_interested=True).count()
            user_part = EventParticipation.query.filter_by(event_id=e.id, user_id=current_user.id).first()
            is_interested = user_part.is_interested if user_part else False
            want_notification = user_part.want_notification if user_part else False

            pins.append({
                'id': e.id, 'type': 'event',
                'name': e.title, 'description': e.description or '',
                'lat': e.lat, 'lng': e.lng,
                'date': e.date.isoformat() + 'Z',
                'end_date': (e.end_date.isoformat() + 'Z') if e.end_date else None,
                'creator_name': e.creator.name if e.creator else 'Anonymous',
                'is_creator': (e.creator_id == current_user.id),
                'participation_count': part_count,
                'is_interested': is_interested,
                'want_notification': want_notification
            })

    return jsonify(pins)


# ── API: add pin ──────────────────────────────────────────────────────────────

@map_bp.route('/api/pin/add', methods=['POST'])
@login_required
def add_pin():
    data = request.get_json()
    campus_id = data.get('campus_id')
    campus = Campus.query.get(campus_id)

    if not campus:
        return jsonify({'error': 'Campus not found'}), 404

    # Authorization check
    is_admin = _is_admin(campus)
    is_member = is_admin or CampusMember.query.filter_by(user_id=current_user.id, campus_id=campus_id).first() is not None

    if not is_member:
        return jsonify({'error': 'Unauthorized. You must join this campus to add items.'}), 403

    pin_type = data.get('type')
    name = data.get('name', '').strip()
    desc = data.get('description', '').strip()
    lat = data.get('lat')
    lng = data.get('lng')

    if not name:
        return jsonify({'error': 'Name is required.'}), 400

    if pin_type != 'club' and (lat is None or lng is None):
        return jsonify({'error': 'Location is required.'}), 400

    if pin_type == 'club':
        if not is_admin:
            return jsonify({'error': 'Only campus moderators can add clubs.'}), 403
        obj = Club(name=name, description=desc, campus_id=campus_id, lat=lat, lng=lng)
        db.session.add(obj)
        db.session.commit()
        return jsonify({'id': obj.id, 'type': 'club', 'name': name,
                        'description': desc, 'lat': lat, 'lng': lng})

    elif pin_type == 'office':
        if not is_admin:
            return jsonify({'error': 'Only campus moderators can add offices.'}), 403
        obj = Office(name=name, description=desc, campus_id=campus_id, lat=lat, lng=lng)
        db.session.add(obj)
        db.session.commit()
        return jsonify({'id': obj.id, 'type': 'office', 'name': name,
                        'description': desc, 'lat': lat, 'lng': lng})

    elif pin_type == 'event':
        if not is_admin:
            four_days_ago = datetime.utcnow() - timedelta(days=4)
            recent_event = EventCreationLog.query.filter(
                EventCreationLog.user_id == current_user.id,
                EventCreationLog.created_at >= four_days_ago
            ).order_by(EventCreationLog.created_at.desc()).first()

            if recent_event:
                time_passed = datetime.utcnow() - recent_event.created_at
                time_remaining = timedelta(days=4) - time_passed
                
                days = time_remaining.days
                hours = time_remaining.seconds // 3600
                minutes = (time_remaining.seconds % 3600) // 60

                remaining_formatted = ""
                if days > 0:
                    remaining_formatted += f"{days}d, "
                if hours > 0:
                    remaining_formatted += f"{hours}h, "
                remaining_formatted += f"{minutes}m"
                return jsonify({
                    'error': f'Event creation cooldown active: Students can only create one event every 4 days. Please wait {remaining_formatted}.'
                }), 400

        date_str = data.get('date')
        end_date_str = data.get('end_date')
        if not date_str or not end_date_str:
            return jsonify({'error': 'Event start and end times are required.'}), 400
        
        try:
            event_date = parse_utc(date_str)
            event_end_date = parse_utc(end_date_str)
        except (ValueError, TypeError) as val_err:
            return jsonify({'error': f'Invalid date format: {str(val_err)}'}), 400

        # Validate start date is not in the past (allowing 5 minutes clock-drift buffer)
        now_naive = datetime.utcnow()
        if event_date < now_naive:
            time_diff = now_naive - event_date
            if time_diff.total_seconds() > 300: # Greater than 5 minutes
                return jsonify({'error': 'Event start time cannot be in the past.'}), 400

        if event_end_date <= event_date:
            return jsonify({'error': 'End time must be after the start time.'}), 400

        obj = Event(
            title=name,
            description=desc,
            campus_id=campus_id,
            creator_id=current_user.id,
            date=event_date,
            end_date=event_end_date,
            lat=lat,
            lng=lng,
            created_at=datetime.utcnow()
        )
        db.session.add(obj)
        
        # Log event creation for students
        if not is_admin:
            log = EventCreationLog(user_id=current_user.id, created_at=datetime.utcnow())
            db.session.add(log)

        db.session.commit()
        return jsonify({
            'id': obj.id,
            'type': 'event',
            'name': name,
            'description': desc,
            'lat': lat,
            'lng': lng,
            'date': event_date.isoformat() + 'Z',
            'end_date': event_end_date.isoformat() + 'Z',
            'creator_name': current_user.name,
            'is_creator': True
        })

    return jsonify({'error': 'Unknown pin type'}), 400


# ── API: delete pin ───────────────────────────────────────────────────────────

@map_bp.route('/api/pin/delete/<pin_type>/<int:pin_id>', methods=['DELETE'])
@login_required
def delete_pin(pin_type, pin_id):
    if pin_type == 'club':
        obj = Club.query.get_or_404(pin_id)
    elif pin_type == 'office':
        obj = Office.query.get_or_404(pin_id)
    elif pin_type == 'event':
        obj = Event.query.get_or_404(pin_id)
    else:
        return jsonify({'error': 'Unknown type'}), 400

    campus_id = obj.campus_id

    campus = Campus.query.get(campus_id)
    if not campus:
        return jsonify({'error': 'Campus not found'}), 404

    allowed = False
    if _is_admin(campus):
        allowed = True
    if pin_type == 'event' and obj.creator_id == current_user.id:
        allowed = True

    if not allowed:
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(obj)
    db.session.commit()
    return jsonify({'success': True})


# ── API: set campus center ────────────────────────────────────────────────────

@map_bp.route('/api/campus/set-center', methods=['POST'])
@login_required
def set_center():
    data = request.get_json()
    campus = Campus.query.get(data.get('campus_id'))
    if not campus or campus.creator_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    campus.center_lat = data.get('lat')
    campus.center_lng = data.get('lng')
    db.session.commit()
    return jsonify({'success': True})


# ── API: toggle event interest / notify me ────────────────────────────────────

@map_bp.route('/api/event/<int:event_id>/interest', methods=['POST'])
@login_required
def toggle_event_interest(event_id):
    event = Event.query.get_or_404(event_id)
    data = request.get_json() or {}
    action = data.get('action') # 'interested' or 'notify'

    participation = EventParticipation.query.filter_by(event_id=event_id, user_id=current_user.id).first()

    if not participation:
        participation = EventParticipation(event_id=event_id, user_id=current_user.id)
        db.session.add(participation)

    if action == 'interested':
        participation.is_interested = not participation.is_interested
        # If no longer interested, also clear notify subscription
        if not participation.is_interested:
            participation.want_notification = False
    elif action == 'notify':
        participation.want_notification = not participation.want_notification
        # Notify subscription automatically registers interest
        if participation.want_notification:
            participation.is_interested = True
            # If the event has already started or ended, mark as already notified to prevent retroactive start alerts
            if event.date <= datetime.utcnow():
                participation.notification_sent = True
            else:
                participation.notification_sent = False

    db.session.commit()

    interest_count = EventParticipation.query.filter_by(event_id=event_id, is_interested=True).count()

    return jsonify({
        'success': True,
        'is_interested': participation.is_interested,
        'want_notification': participation.want_notification,
        'participation_count': interest_count
    })
