// ── Image previews ────────────────────────────────────────────────────────────

// Shows a live preview of the banner image as soon as the user selects a file,
// before they submit the form — uses FileReader to read it locally
document.getElementById('banner_image').addEventListener('change', function () {
    const placeholder = document.getElementById('bannerPlaceholder');
    const img = document.getElementById('bannerImg');
    if (this.files && this.files[0]) {
        const reader = new FileReader();
        reader.onload = e => {
            img.src = e.target.result;          // set image src to the local file data URL
            img.classList.remove('cs-hidden');
            if (placeholder) placeholder.classList.add('cs-hidden');
        };
        reader.readAsDataURL(this.files[0]);    // reads file as base64 data URL
    }
});

// Same live preview for the campus map image
document.getElementById('map_image').addEventListener('change', function () {
    const placeholder = document.getElementById('mapPlaceholder');
    const img = document.getElementById('mapImg');
    if (this.files && this.files[0]) {
        const reader = new FileReader();
        reader.onload = e => {
            img.src = e.target.result;
            img.classList.remove('cs-hidden');
            if (placeholder) placeholder.classList.add('cs-hidden');
        };
        reader.readAsDataURL(this.files[0]);
    }
});

// ── Live name/description preview ─────────────────────────────────────────────

// Updates the campus name preview card in real time as the user types in the name field
document.getElementById('name').addEventListener('input', function () {
    document.getElementById('previewName').textContent = this.value || 'New Campus';
});

// Updates the campus description preview card in real time
document.getElementById('description').addEventListener('input', function () {
    document.getElementById('previewDesc').textContent = this.value || 'Description will appear here...';
});

// ── Delete campus overlay ─────────────────────────────────────────────────────

// Shows a confirmation overlay before deleting the campus (prevents accidental deletion)
const csOverlay = document.getElementById('deleteCampusOverlay');
document.getElementById('openDeleteOverlay').addEventListener('click', () => csOverlay.classList.add('open'));
document.getElementById('cancelDelete').addEventListener('click',      () => csOverlay.classList.remove('open'));
document.getElementById('confirmDelete').addEventListener('click',     () => document.getElementById('deleteCampusForm').submit());

// ── Revoke moderator confirmation ─────────────────────────────────────────────

// Shows a browser confirm dialog before revoking a moderator's role.
// Uses the moderator's name from data-confirm-name for a clear message
document.querySelectorAll('.cs-revoke-form').forEach(form => {
    form.addEventListener('submit', e => {
        const name = form.dataset.confirmName;
        if (!confirm(`Are you sure you want to revoke moderator privileges for ${name}?`)) {
            e.preventDefault();  // cancel form submission if user clicks "Cancel"
        }
    });
});
