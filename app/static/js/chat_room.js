const msgList = document.getElementById('msgList');
const CAMPUS_ID = parseInt(msgList.dataset.campusId);
const ROOM_ID = parseInt(msgList.dataset.roomId);
let lastId = parseInt(msgList.dataset.lastId) || 0;
let lastSender = msgList.dataset.lastSender || null;
let lastMine = msgList.dataset.lastMine === 'true';

msgList.scrollTop = msgList.scrollHeight;

function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function fmtTime(d) {
    let h = d.getHours();
    let m = d.getMinutes();
    let ampm = 'AM';
    if (h >= 12) {
        ampm = 'PM';
    }
    h = h % 12;
    if (h === 0) {
        h = 12;
    }
    return h + ':' + String(m).padStart(2, '0') + ' ' + ampm;
}

function appendMsg(body, sender, mine, id, consecutive) {
    const time = fmtTime(new Date());
    const row = document.createElement('div');
    let rowClass = 'msg-row ';
    if (mine) {
        rowClass = rowClass + 'msg-row-mine';
    } else {
        rowClass = rowClass + 'msg-row-other';
    }
    if (consecutive) {
        rowClass = rowClass + ' msg-consecutive';
    }
    row.className = rowClass;

    let avatarHtml = '';
    if (consecutive) {
        avatarHtml = '<div class="msg-avatar-spacer"></div>';
    } else {
        let avatarClass = '';
        if (mine) {
            avatarClass = 'msg-avatar-mine';
        } else {
            avatarClass = 'msg-avatar-other';
        }
        avatarHtml = '<div class="msg-avatar ' + avatarClass + '">' + esc(sender[0].toUpperCase()) + '</div>';
    }

    let senderHtml = '';
    if (!consecutive && !mine) {
        senderHtml = '<div class="msg-sender">' + esc(sender) + '</div>';
    }

    let msgClass = '';
    if (mine) {
        msgClass = 'msg-mine';
    } else {
        msgClass = 'msg-other';
    }
    row.innerHTML = `${avatarHtml}
        <div class="msg-col">
            ${senderHtml}
            <div class="msg ${msgClass}">
                ${esc(body)}<span class="msg-time">${time}</span>
            </div>
        </div>`;

    msgList.appendChild(row);
    msgList.scrollTop = msgList.scrollHeight;
    lastSender = sender;
    lastMine = mine;
    if (id) {
        lastId = id;
    }
}

async function sendMsg() {
    const inp = document.getElementById('msgInput');
    const body = inp.value.trim();
    if (!body) {
        return;
    }
    inp.value = '';
    const consecutive = lastMine === true;
    const res = await fetch(`/campus/${CAMPUS_ID}/chat/${ROOM_ID}/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ body: body })
    });
    const data = await res.json();
    if (data.id) {
        appendMsg(data.body, data.sender, true, data.id, consecutive);
    }
}

async function poll() {
    try {
        const res = await fetch(`/campus/${CAMPUS_ID}/chat/${ROOM_ID}/poll?after=${lastId}`);
        const msgs = await res.json();
        for (const m of msgs) {
            if (!m.mine) {
                const consecutive = !lastMine && lastSender === m.sender;
                appendMsg(m.body, m.sender, false, m.id, consecutive);
            }
            if (m.id > lastId) {
                lastId = m.id;
            }
        }
    } catch {}
}

setInterval(poll, 3000);

async function confirmLeave() {
    const res = await fetch(`/campus/${CAMPUS_ID}/chat/${ROOM_ID}/leave`, { method: 'POST' });
    if (res.ok) {
        window.location.href = `/campus/${CAMPUS_ID}/chat`;
    }
}

async function confirmDelete() {
    const res = await fetch(`/campus/${CAMPUS_ID}/chat/${ROOM_ID}/delete`, { method: 'POST' });
    if (res.ok) {
        window.location.href = `/campus/${CAMPUS_ID}/chat`;
    }
}

// Overlay wiring
document.getElementById('triggerLeaveBtn').addEventListener('click', () => {
    document.getElementById('leaveOverlay').classList.add('open');
});
document.getElementById('cancelLeaveBtn').addEventListener('click', () => {
    document.getElementById('leaveOverlay').classList.remove('open');
});
document.getElementById('confirmLeaveBtn').addEventListener('click', confirmLeave);

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

document.getElementById('msgInput').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMsg();
    }
});
document.getElementById('sendBtn').addEventListener('click', sendMsg);
