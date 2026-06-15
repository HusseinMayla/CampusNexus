const postFeed  = document.getElementById('postFeed');
const CAMPUS_ID = parseInt(postFeed.dataset.campusId);
const USER_INIT = postFeed.dataset.userInitial;
const EMAIL_RE  = /^[\w.+\-]+@[\w\-]+(\.[a-zA-Z]{2,}){1,3}$/;

let selRole = null, selMethod = null, courses = [];

function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

/* ── Modal ─────────────────────────────────────────────────── */
function openModal() {
    document.getElementById('modalOverlay').classList.add('open');
    document.getElementById('f-name').focus();
}
function closeModal() {
    document.getElementById('modalOverlay').classList.remove('open');
    resetForm();
}
function resetForm() {
    document.getElementById('f-name').value  = '';
    document.getElementById('f-email').value = '';
    selRole = selMethod = null;
    courses = [];
    document.querySelectorAll('.choice-btn').forEach(b => b.classList.remove('sel'));
    document.getElementById('courseWrap').querySelectorAll('.ctag').forEach(t => t.remove());
    document.getElementById('courseInput').value = '';
    ['name', 'email', 'role', 'courses', 'method', 'general'].forEach(k => {
        document.getElementById('err-' + k).textContent = '';
    });
    document.getElementById('submitBtn').disabled = true;
}

/* ── Choice buttons (event delegation per group) ───────────── */
document.querySelectorAll('.choice-group').forEach(group => {
    group.addEventListener('click', e => {
        const btn = e.target.closest('.choice-btn');
        if (!btn) return;
        group.querySelectorAll('.choice-btn').forEach(b => b.classList.remove('sel'));
        btn.classList.add('sel');
        if (group.dataset.group === 'role')   selRole   = btn.dataset.val;
        if (group.dataset.group === 'method') selMethod = btn.dataset.val;
        validate();
    });
});

/* ── Course tags ────────────────────────────────────────────── */
function courseKey(e) {
    const inp = document.getElementById('courseInput');
    if (e.key === 'Enter' && inp.value.trim()) {
        e.preventDefault();
        addCourse(inp.value.trim());
        inp.value = '';
        validate();
    } else if (e.key === 'Backspace' && !inp.value && courses.length) {
        removeCourse(courses.length - 1);
    }
}
function addCourse(val) {
    const idx = courses.length;
    courses.push(val);
    const inp = document.getElementById('courseInput');
    const tag = document.createElement('span');
    tag.className = 'ctag';
    tag.dataset.idx = idx;
    tag.innerHTML = `${esc(val)}<span class="ctag-x">×</span>`;
    tag.querySelector('.ctag-x').addEventListener('click', () => removeCourse(idx));
    document.getElementById('courseWrap').insertBefore(tag, inp);
}
function removeCourse(idx) {
    courses.splice(idx, 1);
    document.getElementById('courseWrap').querySelectorAll('.ctag').forEach(t => t.remove());
    const copy = [...courses];
    courses = [];
    copy.forEach(v => addCourse(v));
    document.getElementById('courseInput').focus();
    validate();
}

/* ── Validation ─────────────────────────────────────────────── */
function validate() {
    let ok   = true;
    const name  = document.getElementById('f-name').value.trim();
    const email = document.getElementById('f-email').value.trim();

    if (name.length > 0 && name.length < 2) {
        document.getElementById('err-name').textContent = 'Min 2 characters.';
        ok = false;
    } else {
        document.getElementById('err-name').textContent = '';
    }
    if (!name) ok = false;

    if (email && !EMAIL_RE.test(email)) {
        document.getElementById('err-email').textContent = 'Enter a valid university email.';
        ok = false;
    } else {
        document.getElementById('err-email').textContent = '';
    }
    if (!email) ok = false;

    if (!selRole || !selMethod || courses.length === 0) ok = false;
    document.getElementById('submitBtn').disabled = !ok;
    return ok;
}

/* ── Submit ─────────────────────────────────────────────────── */
async function submitPost() {
    if (!validate()) return;
    const btn = document.getElementById('submitBtn');
    btn.disabled = true;
    try {
        const res  = await fetch(`/campus/${CAMPUS_ID}/market/post`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                full_name: document.getElementById('f-name').value.trim(),
                email:     document.getElementById('f-email').value.trim(),
                role: selRole, courses, method: selMethod
            })
        });
        const data = await res.json();
        if (!res.ok) {
            document.getElementById('err-general').textContent = data.error || 'Something went wrong.';
            btn.disabled = false;
            return;
        }
        prependCard(data);
        closeModal();
        ensureComposeBar();
    } catch {
        document.getElementById('err-general').textContent = 'Network error. Try again.';
        btn.disabled = false;
    }
}

/* ── Card builder ───────────────────────────────────────────── */
function prependCard(post) {
    const card = document.createElement('div');
    card.className    = 'post-card';
    card.dataset.role = post.role;
    card.dataset.id   = post.id;
    const roleCls    = post.role === 'tutor' ? 'tag-tutor' : 'tag-student';
    const courseTags = post.courses.map(c => `<span class="tag tag-course">${esc(c)}</span>`).join('');
    const initial    = esc(post.poster_name.charAt(0).toUpperCase());
    card.innerHTML = `
        <button class="post-delete-btn" data-post-id="${post.id}" title="Delete post">✕</button>
        <div class="post-header">
            <div class="post-avatar">${initial}</div>
            <span class="post-username">${esc(post.poster_name)}</span>
        </div>
        <hr class="post-divider">
        <div class="post-body">
            <div class="post-row"><span class="tag ${roleCls}">${cap(post.role)}</span></div>
            <div class="post-row">${courseTags}</div>
            <div class="post-row"><span class="tag tag-method">${esc(post.method)}</span></div>
            <div class="post-row"><a href="mailto:${esc(post.email)}" class="tag tag-email">${esc(post.email)}</a></div>
        </div>`;
    postFeed.prepend(card);
    applyFilter();
    const empty = document.getElementById('emptyState');
    if (empty) empty.style.display = 'none';
}

function ensureComposeBar() {
    if (document.querySelector('.compose-bar')) return;
    const bar = document.createElement('div');
    bar.className = 'compose-bar';
    bar.innerHTML = `<div class="compose-avatar">${USER_INIT}</div><span class="compose-placeholder">Looking for a tutor or student? Post here…</span>`;
    bar.addEventListener('click', openModal);
    postFeed.before(bar);
}

/* ── Filter ─────────────────────────────────────────────────── */
function applyFilter() {
    const f = document.querySelector('.filter-btn.active')?.dataset.filter || 'all';
    document.querySelectorAll('.post-card').forEach(c => {
        c.style.display = (f === 'all' || c.dataset.role === f) ? '' : 'none';
    });
}

/* ── Confirm delete ─────────────────────────────────────────── */
function openConfirm(id) {
    document.getElementById('confirmOverlay').classList.add('open');
    document.getElementById('confirmYes').onclick = () => doDelete(id);
}
function closeConfirm() {
    document.getElementById('confirmOverlay').classList.remove('open');
}
async function doDelete(id) {
    closeConfirm();
    try {
        const res = await fetch(`/campus/${CAMPUS_ID}/market/post/${id}`, { method: 'DELETE' });
        if (res.ok) {
            document.querySelector(`.post-card[data-id="${id}"]`)?.remove();
            if (!document.querySelector('.post-card')) {
                const empty = document.getElementById('emptyState');
                if (empty) empty.style.display = '';
                document.querySelector('.compose-bar')?.remove();
            }
        }
    } catch { alert('Failed to delete. Try again.'); }
}

/* ── Event wiring ───────────────────────────────────────────── */
document.getElementById('btnOpenModal').addEventListener('click', openModal);
document.getElementById('btnEmptyModal')?.addEventListener('click', openModal);
document.querySelector('.compose-bar')?.addEventListener('click', openModal);

document.getElementById('modalCloseBtn').addEventListener('click', closeModal);
document.getElementById('modalOverlay').addEventListener('click', e => {
    if (e.target === document.getElementById('modalOverlay')) closeModal();
});

document.getElementById('f-name').addEventListener('input', validate);
document.getElementById('f-name').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('submitBtn').click();
});
document.getElementById('f-email').addEventListener('input', validate);
document.getElementById('f-email').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('submitBtn').click();
});

document.getElementById('courseWrap').addEventListener('click', () => document.getElementById('courseInput').focus());
document.getElementById('courseInput').addEventListener('keydown', courseKey);
document.getElementById('courseInput').addEventListener('input', validate);

document.getElementById('submitBtn').addEventListener('click', submitPost);

document.getElementById('confirmNo').addEventListener('click', closeConfirm);

document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        applyFilter();
    });
});

// Delete — event delegation covers initial + dynamically added cards
postFeed.addEventListener('click', e => {
    const btn = e.target.closest('.post-delete-btn');
    if (btn) openConfirm(parseInt(btn.dataset.postId));
});
