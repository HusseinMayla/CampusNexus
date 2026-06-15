const resFeed    = document.getElementById('resFeed');
const CAMPUS_ID  = parseInt(resFeed.dataset.campusId);
const USER_INIT  = resFeed.dataset.userInitial;
const ALLOWED_EXT = ['pdf', 'pptx', 'ppt', 'docx', 'doc', 'xlsx'];
const EMAIL_RE    = /^[\w.+\-]+@[\w\-]+(\.[a-zA-Z]{2,}){1,3}$/;

function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/* ── Share modal ───────────────────────────────────────────── */
let shareChapters = [];

function openShareModal() {
    document.getElementById('shareModal').classList.add('open');
    document.getElementById('f-code').focus();
}
function closeShareModal() {
    document.getElementById('shareModal').classList.remove('open');
    resetShare();
}

function resetShare() {
    document.getElementById('f-code').value = '';
    document.getElementById('f-file').value = '';
    document.getElementById('fileNameDisplay').classList.add('res-hidden');
    document.getElementById('fileDropLabel').classList.remove('res-hidden');
    document.getElementById('fileDrop').classList.remove('has-file');
    ['share-code', 'share-file', 'share-general'].forEach(k => {
        document.getElementById('err-' + k).textContent = '';
    });
    document.getElementById('shareSubmitBtn').disabled = true;
    document.getElementById('shareSubmitBtn').textContent = 'Upload';
    shareChapters = [];
    document.getElementById('shareChapterWrap').querySelectorAll('.chtag').forEach(t => t.remove());
    document.getElementById('shareChapterInput').value = '';
}

function shareChapterKey(e) {
    if (e.key !== 'Enter' && e.key !== ',') return;
    e.preventDefault();
    const inp = document.getElementById('shareChapterInput');
    const val = inp.value.trim();
    if (!val || shareChapters.includes(val)) { inp.value = ''; return; }
    shareChapters.push(val);
    const tag = document.createElement('span');
    tag.className = 'chtag';
    tag.innerHTML = `${esc(val)} <span class="chtag-x">×</span>`;
    tag.querySelector('.chtag-x').addEventListener('click', () => removeShareChapter(tag, val));
    document.getElementById('shareChapterWrap').insertBefore(tag, inp);
    inp.value = '';
}

function removeShareChapter(tagEl, val) {
    shareChapters = shareChapters.filter(c => c !== val);
    tagEl.remove();
}

function onFileChange(input) {
    const file = input.files[0];
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXT.includes(ext)) {
        document.getElementById('err-share-file').textContent = 'File type not allowed.';
        input.value = '';
        return;
    }
    document.getElementById('err-share-file').textContent = '';
    const display = document.getElementById('fileNameDisplay');
    display.textContent = file.name;
    display.classList.remove('res-hidden');
    document.getElementById('fileDropLabel').classList.add('res-hidden');
    document.getElementById('fileDrop').classList.add('has-file');
    validateShare();
}

function validateShare() {
    const ok = document.getElementById('f-code').value.trim().length > 0 &&
               !!document.getElementById('f-file').files[0];
    document.getElementById('shareSubmitBtn').disabled = !ok;
    return ok;
}

async function submitUpload() {
    if (!validateShare()) return;
    const btn = document.getElementById('shareSubmitBtn');
    btn.disabled = true;
    btn.textContent = 'Uploading…';
    const fd = new FormData();
    fd.append('course_code', document.getElementById('f-code').value.trim().toUpperCase());
    fd.append('chapters', shareChapters.join(','));
    fd.append('file', document.getElementById('f-file').files[0]);
    try {
        const res  = await fetch(`/campus/${CAMPUS_ID}/resources/upload`, { method: 'POST', body: fd });
        const data = await res.json();
        if (!res.ok) {
            document.getElementById('err-share-general').textContent = data.error || 'Something went wrong.';
            btn.disabled = false;
            btn.textContent = 'Upload';
            return;
        }
        prependResourceCard(data);
        closeShareModal();
        ensureComposeBar();
    } catch {
        document.getElementById('err-share-general').textContent = 'Network error. Try again.';
        btn.disabled = false;
        btn.textContent = 'Upload';
    }
}

/* ── Request modal ─────────────────────────────────────────── */
let chapters = [];

function openRequestModal() {
    document.getElementById('requestModal').classList.add('open');
    document.getElementById('r-email').focus();
}
function closeRequestModal() {
    document.getElementById('requestModal').classList.remove('open');
    resetRequest();
}

function resetRequest() {
    document.getElementById('r-email').value = '';
    document.getElementById('r-code').value  = '';
    chapters = [];
    document.getElementById('chapterWrap').querySelectorAll('.chtag').forEach(t => t.remove());
    document.getElementById('chapterInput').value = '';
    ['req-email', 'req-code', 'req-chapters', 'req-general'].forEach(k => {
        document.getElementById('err-' + k).textContent = '';
    });
    document.getElementById('requestSubmitBtn').disabled = true;
}

function chapterKey(e) {
    const inp = document.getElementById('chapterInput');
    if (e.key === 'Enter' && inp.value.trim()) {
        e.preventDefault();
        addChapter(inp.value.trim());
        inp.value = '';
    } else if (e.key === 'Backspace' && !inp.value && chapters.length) {
        removeChapter(chapters.length - 1);
    }
}
function addChapter(val) {
    const idx = chapters.length;
    chapters.push(val);
    const inp = document.getElementById('chapterInput');
    const tag = document.createElement('span');
    tag.className = 'chtag';
    tag.dataset.idx = idx;
    tag.innerHTML = `${esc(val)}<span class="chtag-x">×</span>`;
    tag.querySelector('.chtag-x').addEventListener('click', () => removeChapter(idx));
    document.getElementById('chapterWrap').insertBefore(tag, inp);
}
function removeChapter(idx) {
    chapters.splice(idx, 1);
    const wrap = document.getElementById('chapterWrap');
    wrap.querySelectorAll('.chtag').forEach(t => t.remove());
    const copy = [...chapters];
    chapters = [];
    copy.forEach(v => addChapter(v));
    document.getElementById('chapterInput').focus();
}

function validateRequest() {
    const email = document.getElementById('r-email').value.trim();
    const code  = document.getElementById('r-code').value.trim();
    const ok    = EMAIL_RE.test(email) && code.length > 0;
    document.getElementById('requestSubmitBtn').disabled = !ok;
    return ok;
}

async function submitRequest() {
    if (!validateRequest()) return;
    const btn = document.getElementById('requestSubmitBtn');
    btn.disabled = true;
    try {
        const res  = await fetch(`/campus/${CAMPUS_ID}/resources/request`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email:       document.getElementById('r-email').value.trim(),
                course_code: document.getElementById('r-code').value.trim().toUpperCase(),
                chapters
            })
        });
        const data = await res.json();
        if (!res.ok) {
            document.getElementById('err-req-general').textContent = data.error || 'Something went wrong.';
            btn.disabled = false;
            return;
        }
        prependRequestCard(data);
        closeRequestModal();
        ensureComposeBar();
    } catch {
        document.getElementById('err-req-general').textContent = 'Network error. Try again.';
        btn.disabled = false;
    }
}

/* ── Card builders ─────────────────────────────────────────── */
function ftBg(ext) {
    if (ext === 'pdf')  return 'ft-bg-pdf';
    if (ext === 'pptx' || ext === 'ppt') return 'ft-bg-pptx';
    if (ext === 'docx' || ext === 'doc') return 'ft-bg-docx';
    if (ext === 'xlsx') return 'ft-bg-xlsx';
    return 'ft-bg-pdf';
}
function ftLabel(ext) {
    if (ext === 'pptx' || ext === 'ppt') return 'PPT';
    if (ext === 'docx' || ext === 'doc') return 'DOC';
    if (ext === 'xlsx') return 'XLS';
    return (ext || 'FILE').toUpperCase();
}
function ftType(ext) {
    if (ext === 'pdf')  return 'PDF Document';
    if (ext === 'pptx' || ext === 'ppt') return 'PowerPoint';
    if (ext === 'docx' || ext === 'doc') return 'Word Document';
    if (ext === 'xlsx') return 'Excel Spreadsheet';
    return 'File';
}

function prependResourceCard(r) {
    const card = document.createElement('div');
    card.className = 'post-card';
    card.dataset.id   = r.id;
    card.dataset.type = 'resource';
    const initial = esc(r.uploader_name.charAt(0).toUpperCase());
    const dlUrl   = `/campus/${CAMPUS_ID}/resources/${r.id}/download`;
    const chTags  = r.chapters
        ? r.chapters.split(',').filter(c => c.trim()).map(c => `<span class="tag tag-chapter">${esc(c.trim())}</span>`).join('')
        : '';
    card.innerHTML = `
        <button class="post-delete-btn" data-post-id="${r.id}" data-post-type="resource" title="Delete">✕</button>
        <div class="post-header">
            <div class="post-avatar">${initial}</div>
            <span class="post-username">${esc(r.uploader_name)}</span>
        </div>
        <hr class="post-divider">
        <div class="post-body">
            <div class="post-row"><span class="tag tag-course">${esc(r.course_code)}</span></div>
            ${chTags ? `<div class="post-row">${chTags}</div>` : ''}
            <div class="file-card">
                <div class="file-card-icon ${ftBg(r.file_type)}">${ftLabel(r.file_type)}</div>
                <div class="file-card-info">
                    <span class="file-card-name">${esc(r.original_filename)}</span>
                    <span class="file-card-type">${ftType(r.file_type)}</span>
                </div>
                <a href="${dlUrl}" class="file-card-dl" title="Download">↓</a>
            </div>
        </div>`;
    resFeed.prepend(card);
    hideEmpty();
}

function prependRequestCard(r) {
    const card = document.createElement('div');
    card.className = 'post-card';
    card.dataset.id   = r.id;
    card.dataset.type = 'request';
    const initial     = esc(r.poster_name.charAt(0).toUpperCase());
    const chapterTags = r.chapters.map(c => `<span class="tag tag-chapter">${esc(c)}</span>`).join('');
    card.innerHTML = `
        <button class="post-delete-btn" data-post-id="${r.id}" data-post-type="request" title="Delete">✕</button>
        <div class="post-header">
            <div class="post-avatar">${initial}</div>
            <span class="post-username">${esc(r.poster_name)}</span>
        </div>
        <hr class="post-divider">
        <div class="post-body">
            <div class="request-label">Requesting material</div>
            <div class="post-row"><span class="tag tag-course">${esc(r.course_code)}</span></div>
            <div class="post-row"><a href="mailto:${esc(r.email)}" class="tag tag-email">${esc(r.email)}</a></div>
            ${chapterTags ? `<div class="post-row">${chapterTags}</div>` : ''}
        </div>`;
    resFeed.prepend(card);
    hideEmpty();
}

function ensureComposeBar() {
    if (document.querySelector('.compose-bar')) return;
    const bar = document.createElement('div');
    bar.className = 'compose-bar';
    bar.innerHTML = `<div class="compose-avatar">${USER_INIT}</div><span class="compose-placeholder">Have a file to share? Upload it here…</span>`;
    bar.addEventListener('click', openShareModal);
    resFeed.before(bar);
}

function hideEmpty() {
    const empty = document.getElementById('emptyState');
    if (empty) empty.style.display = 'none';
}

/* ── Confirm delete ────────────────────────────────────────── */
function openConfirm(id, type) {
    document.getElementById('confirmOverlay').classList.add('open');
    document.getElementById('confirmYes').onclick = () => doDelete(id, type);
}
function closeConfirm() {
    document.getElementById('confirmOverlay').classList.remove('open');
}

async function doDelete(id, type) {
    closeConfirm();
    const url = type === 'request'
        ? `/campus/${CAMPUS_ID}/resources/request/${id}`
        : `/campus/${CAMPUS_ID}/resources/${id}`;
    try {
        const res = await fetch(url, { method: 'DELETE' });
        if (res.ok) {
            document.querySelector(`.post-card[data-id="${id}"][data-type="${type}"]`)?.remove();
            if (!document.querySelector('.post-card')) {
                const empty = document.getElementById('emptyState');
                if (empty) empty.style.display = '';
                document.querySelector('.compose-bar')?.remove();
            }
        }
    } catch { alert('Failed to delete. Try again.'); }
}

/* ── Event wiring ──────────────────────────────────────────── */
// Header / empty-state buttons
document.getElementById('btnOpenShare').addEventListener('click', openShareModal);
document.getElementById('btnOpenRequest').addEventListener('click', openRequestModal);
document.getElementById('btnEmptyShare')?.addEventListener('click', openShareModal);
document.getElementById('btnEmptyRequest')?.addEventListener('click', openRequestModal);
document.querySelector('.compose-bar')?.addEventListener('click', openShareModal);

// Share modal
document.getElementById('shareCloseBtn').addEventListener('click', closeShareModal);
document.getElementById('shareModal').addEventListener('click', e => {
    if (e.target === document.getElementById('shareModal')) closeShareModal();
});
document.getElementById('f-code').addEventListener('input', validateShare);
document.getElementById('f-code').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('shareSubmitBtn').click();
});
document.getElementById('fileDrop').addEventListener('click', () => document.getElementById('f-file').click());
document.getElementById('f-file').addEventListener('change', e => onFileChange(e.target));
document.getElementById('shareChapterWrap').addEventListener('click', () => document.getElementById('shareChapterInput').focus());
document.getElementById('shareChapterInput').addEventListener('keydown', shareChapterKey);
document.getElementById('shareSubmitBtn').addEventListener('click', submitUpload);

// Request modal
document.getElementById('requestCloseBtn').addEventListener('click', closeRequestModal);
document.getElementById('requestModal').addEventListener('click', e => {
    if (e.target === document.getElementById('requestModal')) closeRequestModal();
});
document.getElementById('r-email').addEventListener('input', validateRequest);
document.getElementById('r-email').addEventListener('keydown', e => { if (e.key === 'Enter') submitRequest(); });
document.getElementById('r-code').addEventListener('input', validateRequest);
document.getElementById('r-code').addEventListener('keydown', e => { if (e.key === 'Enter') submitRequest(); });
document.getElementById('chapterWrap').addEventListener('click', () => document.getElementById('chapterInput').focus());
document.getElementById('chapterInput').addEventListener('keydown', chapterKey);
document.getElementById('requestSubmitBtn').addEventListener('click', submitRequest);

// Confirm overlay
document.getElementById('confirmNo').addEventListener('click', closeConfirm);

// Delete buttons — event delegation covers both initial and dynamically added cards
resFeed.addEventListener('click', e => {
    const btn = e.target.closest('.post-delete-btn');
    if (btn) openConfirm(parseInt(btn.dataset.postId), btn.dataset.postType);
});
