const msgList   = document.getElementById('msgList');
const CAMPUS_ID = parseInt(msgList.dataset.campusId);
const ROOM_ID   = parseInt(msgList.dataset.roomId);
const MY_NAME   = msgList.dataset.myName;

let lastSender = null;
let lastMine   = false;

function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function appendMsg(body, sender, mine, time, consecutive) {
    const row = document.createElement('div');
    row.className = 'msg-row ' + (mine ? 'msg-row-mine' : 'msg-row-other') +
                    (consecutive ? ' msg-consecutive' : '');
    const avatarHtml = consecutive
        ? `<div class="msg-avatar-spacer"></div>`
        : `<div class="msg-avatar ${mine ? 'msg-avatar-mine' : 'msg-avatar-other'}">${esc(sender[0].toUpperCase())}</div>`;
    const senderHtml = (!consecutive && !mine)
        ? `<div class="msg-sender">${esc(sender)}</div>` : '';
    row.innerHTML = `${avatarHtml}
        <div class="msg-col">
            ${senderHtml}
            <div class="msg ${mine ? 'msg-mine' : 'msg-other'}">
                ${esc(body)}<span class="msg-time">${esc(time)}</span>
            </div>
        </div>`;
    msgList.appendChild(row);
    msgList.scrollTop = msgList.scrollHeight;
    lastSender = sender;
    lastMine   = mine;
}

const socket = io();

socket.on('connect', () => {
    socket.emit('join_study_room', { room_id: ROOM_ID });
});

socket.on('study_history', msgs => {
    msgList.innerHTML = '';
    lastSender = null;
    lastMine   = false;
    msgs.forEach(m => {
        const consecutive = lastSender === m.sender && lastMine === m.mine;
        appendMsg(m.body, m.sender, m.mine, m.time, consecutive);
    });
});

socket.on('study_msg', m => {
    const consecutive = lastSender === m.sender && lastMine === m.mine;
    appendMsg(m.body, m.sender, m.mine, m.time, consecutive);
});

function sendMsg() {
    const inp  = document.getElementById('msgInput');
    const body = inp.value.trim();
    if (!body) return;
    inp.value = '';
    socket.emit('send_study_msg', { room_id: ROOM_ID, body });
}

async function confirmLeave() {
    socket.emit('leave_study_room', { room_id: ROOM_ID });
    const res = await fetch(`/campus/${CAMPUS_ID}/study-rooms/${ROOM_ID}/leave`, { method: 'POST' });
    if (res.ok) window.location.href = `/campus/${CAMPUS_ID}/study-rooms`;
}

async function confirmDelete() {
    const res = await fetch(`/campus/${CAMPUS_ID}/study-rooms/${ROOM_ID}/delete`, { method: 'POST' });
    if (res.ok) window.location.href = `/campus/${CAMPUS_ID}/study-rooms`;
}

// Overlay wiring
document.getElementById('triggerLeaveBtn').addEventListener('click', () => {
    document.getElementById('leaveOverlay').classList.add('open');
});
document.getElementById('cancelLeaveBtn').addEventListener('click', () => {
    document.getElementById('leaveOverlay').classList.remove('open');
});
document.getElementById('confirmLeaveBtn').addEventListener('click', confirmLeave);

document.getElementById('msgInput').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); }
});
document.getElementById('sendBtn').addEventListener('click', sendMsg);

const triggerDeleteBtn = document.getElementById('triggerDeleteBtn');
if (triggerDeleteBtn) {
    triggerDeleteBtn.addEventListener('click', () => {
        document.getElementById('deleteOverlay').classList.add('open');
    });
    document.getElementById('cancelDeleteBtn').addEventListener('click', () => {
        document.getElementById('deleteOverlay').classList.remove('open');
    });
    document.getElementById('confirmDeleteBtn').addEventListener('click', confirmDelete);
}
