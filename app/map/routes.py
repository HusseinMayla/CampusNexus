from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Campus, Club, Office, Event, CampusMember, EventParticipation, EventCreationLog
from datetime import datetime, timedelta, timezone
from app.main.routes import get_sidebar_data  # Reuses sidebar data builder from main blueprint


# Parses an ISO 8601 datetime string (from JavaScript) into a naive UTC datetime.
# Handles the 'Z' suffix that JS Date.toISOString() appends (e.g. "2026-06-25T14:00:00Z")
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


# Returns True if the current user is the campus creator, owner, or moderator
def _is_admin(campus):
    membership = CampusMember.query.filter_by(user_id=current_user.id, campus_id=campus.id).first()
    return campus.creator_id == current_user.id or (membership and membership.role in ('moderator', 'owner'))


# Builds the list of all map pins (clubs, offices, events) for a given campus.
# Events that ended more than 1 hour ago are excluded.
# Each pin dict contains all data the frontend needs to render the popup
def get_map_pins(campus_id):
    pins = []

    # 1. Clubs
    for c in Club.query.filter_by(campus_id=campus_id).all():
        if c.x is not None and c.y is not None:
            pins.append({
                'id': c.id, 'type': 'club',
                'name': c.name, 'description': c.description or '',
                'x': c.x, 'y': c.y
            })

    # 2. Offices
    for o in Office.query.filter_by(campus_id=campus_id).all():
        if o.x is not None and o.y is not None:
            pins.append({
                'id': o.id, 'type': 'office',
                'name': o.name, 'description': o.description or '',
                'x': o.x, 'y': o.y
            })

    # 3. Events (excluding those ended for more than 1 hour)
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    for e in Event.query.filter(Event.campus_id == campus_id, Event.end_date >= one_hour_ago).all():
        if e.x is not None and e.y is not None:
            part_count = EventParticipation.query.filter_by(event_id=e.id, is_interested=True).count()
            user_part = EventParticipation.query.filter_by(event_id=e.id, user_id=current_user.id).first()
            is_interested = False
            if user_part:
                is_interested = user_part.is_interested

            want_notification = False
            if user_part:
                want_notification = user_part.want_notification

            now = datetime.utcnow()
            is_active = e.date <= now <= e.end_date
            is_ended = now > e.end_date

            # Format duration: e.g. "Jun 24, 03:00 PM - 04:00 PM"
            if e.date.date() == e.end_date.date():
                formatted_duration = f"{e.date.strftime('%b %d')}, {e.date.strftime('%I:%M %p').lstrip('0')} - {e.end_date.strftime('%I:%M %p').lstrip('0')}"
            else:
                formatted_duration = f"{e.date.strftime('%b %d %I:%M %p').lstrip('0')} - {e.end_date.strftime('%b %d %I:%M %p').lstrip('0')}"

            end_date_val = None
            if e.end_date:
                end_date_val = e.end_date.isoformat() + 'Z'

            creator_name_val = 'Anonymous'
            if e.creator:
                creator_name_val = e.creator.name

            pins.append({
                'id': e.id, 'type': 'event',
                'name': e.title, 'description': e.description or '',
                'x': e.x, 'y': e.y,
                'date': e.date.isoformat() + 'Z',
                'end_date': end_date_val,
                'creator_name': creator_name_val,
                'is_creator': (e.creator_id == current_user.id),
                'participation_count': part_count,
                'is_interested': is_interested,
                'want_notification': want_notification,
                'is_active': is_active,
                'is_ended': is_ended,
                'formatted_duration': formatted_duration
            })

    return pins


# ── Page ──────────────────────────────────────────────────────────────────────

# Renders the campus map page. `?view=events` switches the active nav tab to events
@map_bp.route('/campus/<int:campus_id>/map')
@login_required
def campus_map(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    is_admin = _is_admin(campus)
    view = request.args.get('view')
    active_page = 'map'
    if view == 'events':
        active_page = 'events'
    pins_data = get_map_pins(campus_id)
    return render_template('main/campus_map.html', campus=campus, is_admin=is_admin, active_page=active_page, pins_data=pins_data, **get_sidebar_data())


# ── Page Actions: add pin / delete pin / interest ─────────────────────────────

# Adds a club, office, or event pin to the map.
# - Clubs and offices: admin/moderator only
# - Events: any member, but students are limited to 1 event every 4 days
@map_bp.route('/campus/<int:campus_id>/pin/add', methods=['POST'])
@login_required
def add_pin(campus_id):
    campus = Campus.query.get_or_404(campus_id)

    # Authorization check
    is_admin = _is_admin(campus)
    is_member = is_admin or CampusMember.query.filter_by(user_id=current_user.id, campus_id=campus_id).first() is not None

    if not is_member:
        flash('Unauthorized. You must join this campus to add items.', 'error')
        return redirect(url_for('map.campus_map', campus_id=campus_id))

    pin_type = request.form.get('type')
    name = request.form.get('name', '').strip()
    desc = request.form.get('description', '').strip()

    # Parse x/y coordinates (pixel position on the campus image map)
    x_val = request.form.get('x')
    y_val = request.form.get('y')
    x = None
    if x_val:
        x = float(x_val)
    y = None
    if y_val:
        y = float(y_val)

    if not name:
        flash('Name is required.', 'error')
        return redirect(url_for('map.campus_map', campus_id=campus_id))

    if pin_type != 'club' and (x is None or y is None):
        flash('Location is required.', 'error')
        return redirect(url_for('map.campus_map', campus_id=campus_id))

    if pin_type == 'club':
        if not is_admin:
            flash('Only campus moderators can add clubs.', 'error')
            return redirect(url_for('map.campus_map', campus_id=campus_id))
        obj = Club(name=name, description=desc, campus_id=campus_id, x=x, y=y)
        db.session.add(obj)
        db.session.commit()
        flash(f'Club "{name}" added successfully!', 'success')

    elif pin_type == 'office':
        if not is_admin:
            flash('Only campus moderators can add offices.', 'error')
            return redirect(url_for('map.campus_map', campus_id=campus_id))
        obj = Office(name=name, description=desc, campus_id=campus_id, x=x, y=y)
        db.session.add(obj)
        db.session.commit()
        flash(f'Office "{name}" added successfully!', 'success')

    elif pin_type == 'event':
        # Students can only create one event every 4 days — check the creation log
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
                flash(f'Event creation cooldown active: Students can only create one event every 4 days. Please wait {remaining_formatted}.', 'error')
                return redirect(url_for('map.campus_map', campus_id=campus_id))

        date_str = request.form.get('date')
        end_date_str = request.form.get('end_date')
        if not date_str or not end_date_str:
            flash('Event start and end times are required.', 'error')
            return redirect(url_for('map.campus_map', campus_id=campus_id))

        try:
            event_date = parse_utc(date_str)
            event_end_date = parse_utc(end_date_str)
        except (ValueError, TypeError) as val_err:
            flash(f'Invalid date format: {str(val_err)}', 'error')
            return redirect(url_for('map.campus_map', campus_id=campus_id))

        # Validate start date is not in the past (allowing 5 minutes clock-drift buffer)
        now_naive = datetime.utcnow()
        if event_date < now_naive:
            time_diff = now_naive - event_date
            if time_diff.total_seconds() > 300: # Greater than 5 minutes
                flash('Event start time cannot be in the past.', 'error')
                return redirect(url_for('map.campus_map', campus_id=campus_id))

        if event_end_date <= event_date:
            flash('End time must be after the start time.', 'error')
            return redirect(url_for('map.campus_map', campus_id=campus_id))

        obj = Event(
            title=name,
            description=desc,
            campus_id=campus_id,
            creator_id=current_user.id,
            date=event_date,
            end_date=event_end_date,
            x=x,
            y=y,
            created_at=datetime.utcnow()
        )
        db.session.add(obj)

        # Log event creation for students (used to enforce the 4-day cooldown)
        if not is_admin:
            log = EventCreationLog(user_id=current_user.id, created_at=datetime.utcnow())
            db.session.add(log)

        db.session.commit()
        flash(f'Event "{name}" scheduled successfully!', 'success')

    return redirect(url_for('map.campus_map', campus_id=campus_id))


# Deletes a pin (club, office, or event).
# Admins can delete any pin. Event creators can delete their own events
@map_bp.route('/campus/<int:campus_id>/pin/delete/<pin_type>/<int:pin_id>', methods=['POST'])
@login_required
def delete_pin(campus_id, pin_type, pin_id):
    if pin_type == 'club':
        obj = Club.query.get_or_404(pin_id)
    elif pin_type == 'office':
        obj = Office.query.get_or_404(pin_id)
    elif pin_type == 'event':
        obj = Event.query.get_or_404(pin_id)
    else:
        flash('Unknown type', 'error')
        return redirect(url_for('map.campus_map', campus_id=campus_id))

    if obj.campus_id != campus_id:
        flash('Invalid campus association', 'error')
        return redirect(url_for('map.campus_map', campus_id=campus_id))

    campus = Campus.query.get(campus_id)
    if not campus:
        flash('Campus not found', 'error')
        return redirect(url_for('map.campus_map', campus_id=campus_id))

    allowed = False
    if _is_admin(campus):
        allowed = True
    if pin_type == 'event' and obj.creator_id == current_user.id:
        allowed = True

    if not allowed:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('map.campus_map', campus_id=campus_id))

    # Use 'title' for events, 'name' for clubs/offices
    name = getattr(obj, 'name', None)
    if not name:
        name = getattr(obj, 'title', 'Item')
    db.session.delete(obj)
    db.session.commit()
    flash(f'{pin_type.capitalize()} "{name}" deleted successfully.', 'success')
    return redirect(url_for('map.campus_map', campus_id=campus_id))


# Toggles the user's interest or notification subscription for an event.
# 'interested': marks/unmarks interest (also clears notify if unmarked)
# 'notify': subscribes/unsubscribes to a start notification (also auto-marks interest)
@map_bp.route('/campus/<int:campus_id>/event/<int:event_id>/interest', methods=['POST'])
@login_required
def toggle_event_interest(campus_id, event_id):
    event = Event.query.get_or_404(event_id)
    action = request.form.get('action') # 'interested' or 'notify'

    participation = EventParticipation.query.filter_by(event_id=event_id, user_id=current_user.id).first()

    # Create participation record if this is the first interaction with this event
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
    return redirect(request.referrer or url_for('map.campus_map', campus_id=campus_id))
