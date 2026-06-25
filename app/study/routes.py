from datetime import datetime, timedelta, timezone  # datetime for timestamps, timedelta for time math (e.g. "2 hours ago"), timezone for converting JS dates to UTC
from flask import render_template, redirect, url_for, request, jsonify, abort, flash, Blueprint  # standard Flask tools — render pages, redirect, build URLs, read form/JSON data, return JSON, abort with error codes, flash messages, blueprint
from flask_login import login_required, current_user  # login_required blocks logged-out users, current_user is the logged-in user object
from app.extensions import db  # database object for queries and saving records
from app.main.routes import get_sidebar_data  # reuses sidebar builder from main blueprint instead of duplicating it
from app.models import (Campus, CampusMember, StudyRoom, StudyRoomMember,
                        StudyRoomMessage, Notification)  # campus/membership for access checks, study room tables for room logic, notifications for alerting room owner

# Parses an ISO 8601 datetime string (from JavaScript) into a naive UTC datetime.
# Handles the 'Z' suffix that JS Date.toISOString() appends (e.g. "2026-06-25T14:00:00Z")
def parse_utc(dt_str):
    if not dt_str:
        return None
    if dt_str.endswith('Z'):
        dt_str = dt_str[:-1] + '+00:00'
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

study_bp = Blueprint('study', __name__)


# Verifies the current user is a campus member before entering any study route. Aborts 403 if not
def _member_or_403(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    if not CampusMember.query.filter_by(user_id=current_user.id, campus_id=campus_id).first():
        abort(403)
    return campus


# Deletes study rooms whose session ended more than 2 hours ago.
# Called before listing rooms so expired rooms never appear in the UI
def delete_old_rooms(campus_id):
    cutoff = datetime.utcnow() - timedelta(hours=2)
    old_rooms = StudyRoom.query.filter(
        StudyRoom.campus_id == campus_id,
        StudyRoom.session_time < cutoff
    ).all()
    for r in old_rooms:
        db.session.delete(r)
    if old_rooms:
        db.session.commit()


# Returns only rooms the user should see:
# - Rooms they're already a member of, OR rooms that still have space
# - Expired rooms are cleaned up first, then filtered out
def _visible_rooms(campus_id, user_id):
    delete_old_rooms(campus_id)
    cutoff = datetime.utcnow() - timedelta(hours=2)
    rooms = StudyRoom.query.filter(
        StudyRoom.campus_id == campus_id,
        StudyRoom.session_time >= cutoff
    ).order_by(StudyRoom.session_time.asc()).all()
    result = []
    for room in rooms:
        is_member = any(m.user_id == user_id for m in room.members)
        if is_member or room.member_count() < room.max_members:
            result.append(room)
    return result


# ── Browse ────────────────────────────────────────────────────────────────────

# Lists all visible study rooms for a campus, with which ones the user has joined
@study_bp.route('/campus/<int:campus_id>/study-rooms')
@login_required
def browse(campus_id):
    campus = _member_or_403(campus_id)
    rooms = _visible_rooms(campus_id, current_user.id)
    joined_ids = []
    for m in StudyRoomMember.query.filter_by(user_id=current_user.id).all():
        joined_ids.append(m.room_id)
    return render_template('study/browse.html', campus=campus, rooms=rooms,
                           joined_ids=joined_ids, active_page='study', **get_sidebar_data())


# ── Create ────────────────────────────────────────────────────────────────────

# Creates a new study room. Validates:
# - Session time is in the future and within 1 week
# - Max members is between 2 and 20
# - User is not already in an active study room in this campus
@study_bp.route('/campus/<int:campus_id>/study-rooms/create', methods=['POST'])
@login_required
def create(campus_id):
    _member_or_403(campus_id)
    data = request.form

    title = data.get('title', '').strip()
    location = data.get('location', '').strip()
    session_time = data.get('session_time', '').strip()
    max_members = data.get('max_members')

    if not title or not location or not session_time or not max_members:
        flash('All fields are required.', 'error')
        return redirect(url_for('study.browse', campus_id=campus_id))

    try:
        session_dt = parse_utc(session_time)
    except (ValueError, TypeError):
        flash('Invalid session time.', 'error')
        return redirect(url_for('study.browse', campus_id=campus_id))

    now = datetime.utcnow()
    # Simple clock-drift buffer for creation
    if session_dt <= now - timedelta(minutes=5):
        flash('Session time must be in the future.', 'error')
        return redirect(url_for('study.browse', campus_id=campus_id))
    if session_dt > now + timedelta(weeks=1):
        flash('Session cannot be more than 1 week away.', 'error')
        return redirect(url_for('study.browse', campus_id=campus_id))

    try:
        max_members = int(max_members)
    except (TypeError, ValueError):
        flash('Invalid max members.', 'error')
        return redirect(url_for('study.browse', campus_id=campus_id))
    if max_members < 2 or max_members > 20:
        flash('Max members must be between 2 and 20.', 'error')
        return redirect(url_for('study.browse', campus_id=campus_id))

    # Block if already a member of an active study room in this campus
    cutoff = datetime.utcnow() - timedelta(hours=2)
    already_in_room = False
    my_memberships = StudyRoomMember.query.filter_by(user_id=current_user.id).all()
    for m in my_memberships:
        other_room = StudyRoom.query.get(m.room_id)
        if other_room and other_room.campus_id == campus_id and other_room.session_time >= cutoff:
            already_in_room = True
            break
    if already_in_room:
        flash('You are already in an active study room.', 'error')
        return redirect(url_for('study.browse', campus_id=campus_id))

    room = StudyRoom(campus_id=campus_id, owner_id=current_user.id,
                     title=title, location=location,
                     session_time=session_dt, max_members=max_members)
    db.session.add(room)
    db.session.commit()
    # Auto-join the creator as the first member
    db.session.add(StudyRoomMember(room_id=room.id, user_id=current_user.id))
    db.session.commit()

    flash(f'Study room "{title}" created!', 'success')
    return redirect(url_for('study.room', campus_id=campus_id, room_id=room.id))


# ── Join ──────────────────────────────────────────────────────────────────────

# Joins a study room. Checks:
# - Room hasn't expired
# - Room isn't full
# - User doesn't already have an overlapping study room at that time
# Notifies the room owner when someone joins
@study_bp.route('/campus/<int:campus_id>/study-rooms/<int:room_id>/join', methods=['POST'])
@login_required
def join(campus_id, room_id):
    _member_or_403(campus_id)
    room = StudyRoom.query.filter_by(id=room_id, campus_id=campus_id).first_or_404()

    if room.is_expired():
        flash('This session has ended.', 'error')
        return redirect(url_for('study.browse', campus_id=campus_id))
    if room.member_count() >= room.max_members:
        flash('Room is full.', 'error')
        return redirect(url_for('study.browse', campus_id=campus_id))
    if StudyRoomMember.query.filter_by(user_id=current_user.id, room_id=room_id).first():
        return redirect(url_for('study.room', campus_id=campus_id, room_id=room_id))

    # Block if user is already in a room with overlapping time (within 2 hour window)
    new_start = room.session_time
    new_end = new_start + timedelta(hours=2)
    my_memberships = StudyRoomMember.query.filter_by(user_id=current_user.id).all()
    for m in my_memberships:
        if m.room_id == room_id:
            continue
        other = StudyRoom.query.get(m.room_id)
        if other and other.session_time > new_start - timedelta(hours=2) and other.session_time < new_end:
            flash('You already have a study room at that time.', 'error')
            return redirect(url_for('study.browse', campus_id=campus_id))

    db.session.add(StudyRoomMember(room_id=room_id, user_id=current_user.id))

    # Notify owner
    if room.owner_id != current_user.id:
        db.session.add(Notification(
            user_id=room.owner_id,
            title='Someone joined your study room',
            message=f'{current_user.name} joined "{room.title}"',
            link=url_for('study.room', campus_id=campus_id, room_id=room_id)
        ))

    db.session.commit()
    flash(f'Joined study room "{room.title}"!', 'success')
    return redirect(url_for('study.room', campus_id=campus_id, room_id=room_id))


# ── Leave ─────────────────────────────────────────────────────────────────────

# Removes the user from the room. If they were the last member, the room is deleted
@study_bp.route('/campus/<int:campus_id>/study-rooms/<int:room_id>/leave', methods=['POST'])
@login_required
def leave(campus_id, room_id):
    srm = StudyRoomMember.query.filter_by(user_id=current_user.id, room_id=room_id).first_or_404()
    db.session.delete(srm)
    db.session.commit()

    # Delete room if no members left
    room = StudyRoom.query.get(room_id)
    if room and room.member_count() == 0:
        db.session.delete(room)
        db.session.commit()
        flash('Left the study room (room deleted because no members remain).', 'success')
    else:
        flash('Left the study room.', 'success')
    return redirect(url_for('study.browse', campus_id=campus_id))


# ── Delete (owner) ────────────────────────────────────────────────────────────

# Deletes the room entirely (owner only). Cascade removes all members and messages
@study_bp.route('/campus/<int:campus_id>/study-rooms/<int:room_id>/delete', methods=['POST'])
@login_required
def delete(campus_id, room_id):
    room = StudyRoom.query.filter_by(id=room_id, campus_id=campus_id).first_or_404()
    if room.owner_id != current_user.id:
        abort(403)
    db.session.delete(room)
    db.session.commit()
    flash(f'Study room "{room.title}" deleted.', 'success')
    return redirect(url_for('study.browse', campus_id=campus_id))


# ── Room chat page ────────────────────────────────────────────────────────────

# Renders the study room chat page. Marks all messages as read on entry.
# Passes last_id to the template so JavaScript knows where to start polling from
@study_bp.route('/campus/<int:campus_id>/study-rooms/<int:room_id>')
@login_required
def room(campus_id, room_id):
    campus = _member_or_403(campus_id)
    delete_old_rooms(campus_id)
    sr = StudyRoom.query.filter_by(id=room_id, campus_id=campus_id).first_or_404()
    srm = StudyRoomMember.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    if not srm:
        return redirect(url_for('study.browse', campus_id=campus_id))

    srm.last_read_at = datetime.utcnow()
    db.session.commit()

    msgs = StudyRoomMessage.query.filter_by(room_id=room_id).order_by(StudyRoomMessage.sent_at.asc()).all()
    if msgs:
        last_id = msgs[-1].id
    else:
        last_id = 0

    return render_template('study/room.html', campus=campus, room=sr,
                           messages=msgs, last_id=last_id, active_page='study', **get_sidebar_data())


# JSON endpoint: receives a message body and saves it. Called by JavaScript, not a form
@study_bp.route('/campus/<int:campus_id>/study-rooms/<int:room_id>/send', methods=['POST'])
@login_required
def send_message(campus_id, room_id):
    srm = StudyRoomMember.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    if not srm:
        return jsonify({'error': 'Not a member'}), 403
    json_data = request.json
    body = ""
    if json_data is not None:
        body = json_data.get('body', '').strip()
    if not body or len(body) > 2000:
        return jsonify({'error': 'Invalid message'}), 400
    msg = StudyRoomMessage(room_id=room_id, sender_id=current_user.id, body=body)
    db.session.add(msg)
    srm.last_read_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'id': msg.id, 'body': msg.body, 'sender': current_user.name})


# JSON endpoint: returns only messages newer than the given ID (used for live polling)
@study_bp.route('/campus/<int:campus_id>/study-rooms/<int:room_id>/poll')
@login_required
def poll_messages(campus_id, room_id):
    srm = StudyRoomMember.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    if not srm:
        return jsonify({'error': 'Not a member'}), 403
    after = request.args.get('after', 0, type=int)
    msgs = StudyRoomMessage.query.filter(
        StudyRoomMessage.room_id == room_id,
        StudyRoomMessage.id > after
    ).order_by(StudyRoomMessage.sent_at.asc()).all()
    if msgs:
        srm.last_read_at = datetime.utcnow()
        db.session.commit()
    result = []
    for m in msgs:
        result.append({
            'id': m.id,
            'body': m.body,
            'sender': m.sender.name,
            'mine': m.sender_id == current_user.id
        })
    return jsonify(result)
