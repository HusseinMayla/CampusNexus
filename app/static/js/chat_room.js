// ── Setup: read data attributes injected by the template into the msgList element ──
const msgList = document.getElementById('msgList');
const CAMPUS_ID = parseInt(msgList.dataset.campusId);   // campus ID for building fetch URLs
const ROOM_ID = parseInt(msgList.dataset.roomId);       // room ID for building fetch URLs
let lastId = parseInt(msgList.dataset.lastId) || 0;     // ID of last message already on screen — polling starts from here
let lastSender = msgList.dataset.lastSender || null;    // tracks who sent the last message (for consecutive grouping)
let lastMine = msgList.dataset.lastMine === 'true';     // tracks if the last message was mine (for consecutive grouping)

// Scroll to the bottom on page load so the latest messages are visible
msgList.scrollTop = msgList.scrollHeight;

// Escapes HTML special characters to prevent XSS when rendering message bodies
function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Formats a Date object as "3:05 PM" style time for the message timestamp
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

// Builds and appends a message bubble to the chat list.
// `consecutive` = true if the same sender sent the previous message — hides the avatar and name to group them visually
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

    // Show avatar initial only for the first message in a group; use a spacer for consecutive ones
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

    // Show sender name only for other people's first message in a group
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
    msgList.scrollTop = msgList.scrollHeight;   // auto-scroll to the new message
    lastSender = sender;
    lastMine = mine;
    if (id) {
        lastId = id;    // update lastId so next poll only fetches newer messages
    }
}

// Sends a message to the server via JSON POST, then appends it to the chat immediately (no wait for poll)
async function sendMsg() {
    const inp = document.getElementById('msgInput');
    const body = inp.value.trim();
    if (!body) {
        return;
    }
    inp.value = '';
    const consecutive = lastMine === true;  // my message follows my previous message
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

// Fetches new messages from the server (only those with id > lastId).
// Skips messages sent by the current user since they're already appended by sendMsg()
async function poll() {
    try {
        const res = await fetch(`/campus/${CAMPUS_ID}/chat/${ROOM_ID}/poll?after=${lastId}`);
        const msgs = await res.json();
        for (const m of msgs) {
            if (!m.mine) {  // skip own messages — already displayed when sent
                const consecutive = !lastMine && lastSender === m.sender;
                appendMsg(m.body, m.sender, false, m.id, consecutive);
            }
            if (m.id > lastId) {
                lastId = m.id;  // advance lastId even for own messages so they aren't re-fetched
            }
        }
    } catch {}  // silently ignore network errors so the chat doesn't crash on a blip
}

// Poll for new messages every 3 seconds
setInterval(poll, 3000);

// Overlay wiring and functions removed since leave/delete are now standard forms.

// Send message on Enter key (Shift+Enter inserts a newline instead)
document.getElementById('msgInput').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMsg();
    }
});
document.getElementById('sendBtn').addEventListener('click', sendMsg);
