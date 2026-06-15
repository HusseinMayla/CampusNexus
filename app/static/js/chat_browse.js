const CAMPUS_ID = parseInt(document.getElementById('roomList').dataset.campusId);

async function joinRoom(id, btn) {
    btn.disabled = true;
    const res  = await fetch(`/campus/${CAMPUS_ID}/chat/${id}/join`, { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
        window.location.href = `/campus/${CAMPUS_ID}/chat/${id}`;
    } else {
        alert(data.error || 'Failed to join.');
        btn.disabled = false;
    }
}

async function createRoom() {
    const inp  = document.getElementById('newRoomName');
    const name = inp.value.trim();
    if (!name) return;
    const res  = await fetch(`/campus/${CAMPUS_ID}/chat/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
    });
    const data = await res.json();
    if (res.ok) {
        window.location.reload();
    } else {
        document.getElementById('createErr').textContent = data.error || 'Failed to create.';
    }
}

// Join buttons — event delegation
document.getElementById('roomList').addEventListener('click', e => {
    const btn = e.target.closest('.btn-join');
    if (btn) joinRoom(parseInt(btn.dataset.roomId), btn);
});

document.getElementById('newRoomName').addEventListener('keydown', e => {
    if (e.key === 'Enter') createRoom();
});
document.getElementById('createBtn').addEventListener('click', createRoom);
