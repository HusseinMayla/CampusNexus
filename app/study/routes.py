from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, request, jsonify, abort, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import (Campus, CampusMember, StudyRoom, StudyRoomMember,
                        StudyRoomMessage, Notification)
from app.study import study_bp


def _member_or_403(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    if not CampusMember.query.filter_by(user_id=current_user.id, campus_id=campus_id).first():
        abort(403)
    return campus


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


def _visible_rooms(campus_id, user_id):
    delete_old_rooms(campus_id)
    cutoff = datetime.utcnow() - timedelta(hours=2)
    rooms = StudyRoom.query.filter(
        StudyRoom.campus_id == campus_id,
        StudyRoom.session_time >= cutoff
    ).order_by(StudyRoom.session_time.asc()).all()
    result = []
    for room in rooms:
        is_member = False
        for m in room.members:
            if m.user_id == user_id:
                is_member = True
                break
        if is_member or room.member_count() < room.max_members:
            result.append(room)
    return result


# ── Browse ────────────────────────────────────────────────────────────────────

@study_bp.route('/campus/<int:campus_id>/study-rooms')
@login_required
def browse(campus_id):
    campus = _member_or_403(campus_id)
    rooms = _visible_rooms(campus_id, current_user.id)
    joined_ids = []
    for m in StudyRoomMember.query.filter_by(user_id=current_user.id).all():
        joined_ids.append(m.room_id)
    return render_template('study/browse.html', campus=campus, rooms=rooms,
                           joined_ids=joined_ids, active_page='study')


# ── Create ────────────────────────────────────────────────────────────────────

@study_bp.route('/campus/<int:campus_id>/study-rooms/create', methods=['POST'])
@login_required
def create(campus_id):
    campus = _member_or_403(campus_id)
    data = request.json or {}

    title = data.get('title', '').strip()
    location = data.get('location', '').strip()
    session_time = data.get('session_time', '').strip()
    max_members = data.get('max_members')

    if not title or not location or not session_time or not max_members:
        return jsonify({'error': 'All fields are required'}), 400

    try:
        session_dt = datetime.fromisoformat(session_time)
    except ValueError:
        return jsonify({'error': 'Invalid session time'}), 400

    now = datetime.utcnow()
    if session_dt <= now:
        return jsonify({'error': 'Session time must be in the future'}), 400
    if session_dt > now + timedelta(weeks=1):
        return jsonify({'error': 'Session cannot be more than 1 week away'}), 400

    try:
        max_members = int(max_members)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid max members'}), 400
    if max_members < 2 or max_members > 20:
        return jsonify({'error': 'Max members must be between 2 and 20'}), 400

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
        return jsonify({'error': 'You are already in an active study room'}), 400

    room = StudyRoom(campus_id=campus_id, owner_id=current_user.id,
                     title=title, location=location,
                     session_time=session_dt, max_members=max_members)
    db.session.add(room)
    db.session.commit()
    db.session.add(StudyRoomMember(room_id=room.id, user_id=current_user.id))
    db.session.commit()

    return jsonify({'id': room.id, 'redirect': url_for('study.room',
                    campus_id=campus_id, room_id=room.id)}), 201


# ── Join ──────────────────────────────────────────────────────────────────────

@study_bp.route('/campus/<int:campus_id>/study-rooms/<int:room_id>/join', methods=['POST'])
@login_required
def join(campus_id, room_id):
    _member_or_403(campus_id)
    room = StudyRoom.query.filter_by(id=room_id, campus_id=campus_id).first_or_404()

    if room.is_expired():
        return jsonify({'error': 'This session has ended'}), 400
    if room.member_count() >= room.max_members:
        return jsonify({'error': 'Room is full'}), 400
    if StudyRoomMember.query.filter_by(user_id=current_user.id, room_id=room_id).first():
        return jsonify({'ok': True, 'redirect': url_for('study.room',
                        campus_id=campus_id, room_id=room_id)})

    # Block if user is already in a room with overlapping time
    new_start = room.session_time
    new_end = new_start + timedelta(hours=2)
    my_memberships = StudyRoomMember.query.filter_by(user_id=current_user.id).all()
    for m in my_memberships:
        if m.room_id == room_id:
            continue
        other = StudyRoom.query.get(m.room_id)
        if other and other.session_time > new_start - timedelta(hours=2) and other.session_time < new_end:
            return jsonify({'error': 'You already have a study room at that time'}), 400

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
    return jsonify({'ok': True, 'redirect': url_for('study.room',
                    campus_id=campus_id, room_id=room_id)})


# ── Leave ─────────────────────────────────────────────────────────────────────

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
    return jsonify({'ok': True})


# ── Delete (owner) ────────────────────────────────────────────────────────────

@study_bp.route('/campus/<int:campus_id>/study-rooms/<int:room_id>/delete', methods=['POST'])
@login_required
def delete(campus_id, room_id):
    room = StudyRoom.query.filter_by(id=room_id, campus_id=campus_id).first_or_404()
    if room.owner_id != current_user.id:
        abort(403)
    db.session.delete(room)
    db.session.commit()
    return jsonify({'ok': True})


# ── Room chat page ────────────────────────────────────────────────────────────

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
                           messages=msgs, last_id=last_id, active_page='study')


@study_bp.route('/campus/<int:campus_id>/study-rooms/<int:room_id>/send', methods=['POST'])
@login_required
def send_message(campus_id, room_id):
    srm = StudyRoomMember.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    if not srm:
        return jsonify({'error': 'Not a member'}), 403
    body = (request.json or {}).get('body', '').strip()
    if not body or len(body) > 2000:
        return jsonify({'error': 'Invalid message'}), 400
    msg = StudyRoomMessage(room_id=room_id, sender_id=current_user.id, body=body)
    db.session.add(msg)
    srm.last_read_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'id': msg.id, 'body': msg.body, 'sender': current_user.name})


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
