from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, request, jsonify, abort, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import (Campus, CampusMember, StudyRoom, StudyRoomMember,
                        StudyRoomMessage, UserCourse, Notification)
from app.study import study_bp


def _member_or_403(campus_id):
    campus = Campus.query.get_or_404(campus_id)
    if not CampusMember.query.filter_by(user_id=current_user.id, campus_id=campus_id).first():
        abort(403)
    return campus


def _cleanup_expired(campus_id):
    cutoff = datetime.utcnow() - timedelta(hours=2)
    expired = StudyRoom.query.filter(
        StudyRoom.campus_id == campus_id,
        StudyRoom.session_time < cutoff
    ).all()
    for r in expired:
        db.session.delete(r)
    if expired:
        db.session.commit()


def _visible_rooms(campus_id, user_id):
    _cleanup_expired(campus_id)
    enrolled = {uc.course_code for uc in
                UserCourse.query.filter_by(user_id=user_id, campus_id=campus_id).all()}
    if not enrolled:
        return []
    cutoff = datetime.utcnow() - timedelta(hours=2)
    rooms = StudyRoom.query.filter(
        StudyRoom.campus_id == campus_id,
        StudyRoom.course_code.in_(enrolled),
        StudyRoom.session_time >= cutoff
    ).order_by(StudyRoom.session_time.asc()).all()
    result = []
    for room in rooms:
        is_member = any(m.user_id == user_id for m in room.members)
        if is_member or room.member_count < room.max_members:
            result.append(room)
    return result


# ── Browse ────────────────────────────────────────────────────────────────────

@study_bp.route('/campus/<int:campus_id>/study-rooms')
@login_required
def browse(campus_id):
    campus = _member_or_403(campus_id)
    rooms  = _visible_rooms(campus_id, current_user.id)
    joined_ids = {m.room_id for m in StudyRoomMember.query.filter_by(user_id=current_user.id).all()}
    my_courses = UserCourse.query.filter_by(user_id=current_user.id, campus_id=campus_id)\
                                 .order_by(UserCourse.course_code).all()
    return render_template('study/browse.html', campus=campus, rooms=rooms,
                           joined_ids=joined_ids, my_courses=my_courses,
                           active_page='study')


# ── Course enrollment ─────────────────────────────────────────────────────────

@study_bp.route('/campus/<int:campus_id>/study-rooms/courses/add', methods=['POST'])
@login_required
def add_course(campus_id):
    _member_or_403(campus_id)
    code = (request.json or {}).get('course_code', '').strip().upper()
    if not code:
        return jsonify({'error': 'Course code required'}), 400
    if UserCourse.query.filter_by(user_id=current_user.id, campus_id=campus_id, course_code=code).first():
        return jsonify({'error': 'Already enrolled'}), 400
    uc = UserCourse(user_id=current_user.id, campus_id=campus_id, course_code=code)
    db.session.add(uc)
    db.session.commit()
    return jsonify({'ok': True, 'course_code': code, 'id': uc.id})


@study_bp.route('/campus/<int:campus_id>/study-rooms/courses/remove/<int:uc_id>', methods=['POST'])
@login_required
def remove_course(campus_id, uc_id):
    uc = UserCourse.query.get_or_404(uc_id)
    if uc.user_id != current_user.id:
        abort(403)
    db.session.delete(uc)
    db.session.commit()
    return jsonify({'ok': True})


# ── Create ────────────────────────────────────────────────────────────────────

@study_bp.route('/campus/<int:campus_id>/study-rooms/create', methods=['POST'])
@login_required
def create(campus_id):
    campus = _member_or_403(campus_id)
    data   = request.json or {}

    course_code  = data.get('course_code', '').strip().upper()
    chapter      = data.get('chapter', '').strip()
    location     = data.get('location', '').strip()
    session_time = data.get('session_time', '').strip()
    max_members  = data.get('max_members')

    if not all([course_code, chapter, location, session_time, max_members]):
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
    if not 2 <= max_members <= 20:
        return jsonify({'error': 'Max members must be between 2 and 20'}), 400

    # Auto-enroll in the course if not already
    if not UserCourse.query.filter_by(user_id=current_user.id, campus_id=campus_id,
                                      course_code=course_code).first():
        db.session.add(UserCourse(user_id=current_user.id, campus_id=campus_id,
                                  course_code=course_code))

    room = StudyRoom(campus_id=campus_id, owner_id=current_user.id,
                     course_code=course_code, chapter=chapter,
                     location=location, session_time=session_dt,
                     max_members=max_members)
    db.session.add(room)
    db.session.flush()
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

    if room.is_expired:
        return jsonify({'error': 'This session has ended'}), 400
    if room.member_count >= room.max_members:
        return jsonify({'error': 'Room is full'}), 400
    if StudyRoomMember.query.filter_by(user_id=current_user.id, room_id=room_id).first():
        return jsonify({'ok': True, 'redirect': url_for('study.room',
                        campus_id=campus_id, room_id=room_id)})

    db.session.add(StudyRoomMember(room_id=room_id, user_id=current_user.id))

    # Notify owner
    if room.owner_id != current_user.id:
        db.session.add(Notification(
            user_id=room.owner_id,
            title='Someone joined your study room',
            message=f'{current_user.name} joined {room.course_code} — {room.chapter}',
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
    db.session.flush()

    # Delete room if no members left
    room = StudyRoom.query.get(room_id)
    if room and room.member_count == 0:
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
    _cleanup_expired(campus_id)
    sr = StudyRoom.query.filter_by(id=room_id, campus_id=campus_id).first_or_404()
    srm = StudyRoomMember.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    if not srm:
        return redirect(url_for('study.browse', campus_id=campus_id))

    srm.last_read_at = datetime.utcnow()
    db.session.commit()

    return render_template('study/room.html', campus=campus, room=sr,
                           active_page='study')
