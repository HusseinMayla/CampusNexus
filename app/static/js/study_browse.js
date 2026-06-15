const CAMPUS_ID = parseInt(document.getElementById('createPanel').dataset.campusId);

async function joinRoom(id, btn) {
    btn.disabled = true;
    const res  = await fetch(`/campus/${CAMPUS_ID}/study-rooms/${id}/join`, { method: 'POST' });
    const data = await res.json();
    if (res.ok) window.location.href = data.redirect;
    else { alert(data.error || 'Failed to join.'); btn.disabled = false; }
}

async function createRoom() {
    const title    = document.getElementById('cr-title').value.trim();
    const location = document.getElementById('cr-location').value.trim();
    const time     = document.getElementById('cr-time').value;
    const max      = document.getElementById('cr-max').value;
    const err      = document.getElementById('createErr');
    err.textContent = '';
    if (!title || !location || !time || !max) {
        err.textContent = 'All fields are required.'; return;
    }
    const res  = await fetch(`/campus/${CAMPUS_ID}/study-rooms/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, location, session_time: time, max_members: parseInt(max) })
    });
    const data = await res.json();
    if (res.ok) window.location.reload();
    else err.textContent = data.error || 'Failed to create.';
}

// Scroll to create panel
document.getElementById('scrollToCreate').addEventListener('click', () => {
    document.getElementById('createPanel').scrollIntoView({ behavior: 'smooth' });
});

// Join buttons — event delegation
const roomList = document.getElementById('roomList');
if (roomList) {
    roomList.addEventListener('click', e => {
        const btn = e.target.closest('.sb-join-btn');
        if (btn) joinRoom(parseInt(btn.dataset.roomId), btn);
    });
}

// Enter key on create inputs
['cr-title', 'cr-location', 'cr-max'].forEach(id => {
    document.getElementById(id).addEventListener('keydown', e => {
        if (e.key === 'Enter') createRoom();
    });
});

document.getElementById('createRoomBtn').addEventListener('click', createRoom);
