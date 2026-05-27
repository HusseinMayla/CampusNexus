from datetime import datetime
from flask import request
from flask_login import current_user
from flask_socketio import join_room, leave_room, emit
from app.extensions import socketio, db
from app.models import StudyRoom, StudyRoomMember, StudyRoomMessage


def _room_key(room_id):
    return f'study_{room_id}'


@socketio.on('join_study_room')
def on_join(data):
    if not current_user.is_authenticated:
        return
    room_id = data.get('room_id')
    srm = StudyRoomMember.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    if not srm:
        return

    join_room(_room_key(room_id))

    srm.last_read_at = datetime.utcnow()
    db.session.commit()

    msgs = StudyRoomMessage.query.filter_by(room_id=room_id)\
                                 .order_by(StudyRoomMessage.sent_at.asc()).all()
    history = [{
        'id':     m.id,
        'body':   m.body,
        'sender': m.sender.name,
        'mine':   m.sender_id == current_user.id,
        'time':   m.sent_at.strftime('%I:%M %p')
    } for m in msgs]
    emit('study_history', history)


@socketio.on('leave_study_room')
def on_leave(data):
    room_id = data.get('room_id')
    leave_room(_room_key(room_id))


@socketio.on('send_study_msg')
def on_message(data):
    if not current_user.is_authenticated:
        return
    room_id = data.get('room_id')
    body    = (data.get('body') or '').strip()
    if not body or len(body) > 2000:
        return

    srm = StudyRoomMember.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    if not srm:
        return

    msg = StudyRoomMessage(room_id=room_id, sender_id=current_user.id, body=body)
    db.session.add(msg)
    srm.last_read_at = datetime.utcnow()
    db.session.commit()

    emit('study_msg', {
        'id':     msg.id,
        'body':   msg.body,
        'sender': current_user.name,
        'mine':   False,
        'time':   msg.sent_at.strftime('%I:%M %p')
    }, to=_room_key(room_id), include_self=False)

    emit('study_msg', {
        'id':     msg.id,
        'body':   msg.body,
        'sender': current_user.name,
        'mine':   True,
        'time':   msg.sent_at.strftime('%I:%M %p')
    })
