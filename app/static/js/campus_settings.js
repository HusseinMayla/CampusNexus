// Banner image preview
document.getElementById('banner_image').addEventListener('change', function () {
    const placeholder = document.getElementById('bannerPlaceholder');
    const img = document.getElementById('bannerImg');
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

// Map image preview
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

// Live name/desc preview
document.getElementById('name').addEventListener('input', function () {
    document.getElementById('previewName').textContent = this.value || 'New Campus';
});
document.getElementById('description').addEventListener('input', function () {
    document.getElementById('previewDesc').textContent = this.value || 'Description will appear here...';
});

// Delete campus overlay
const csOverlay = document.getElementById('deleteCampusOverlay');
document.getElementById('openDeleteOverlay').addEventListener('click', () => csOverlay.classList.add('open'));
document.getElementById('cancelDelete').addEventListener('click',      () => csOverlay.classList.remove('open'));
document.getElementById('confirmDelete').addEventListener('click',     () => document.getElementById('deleteCampusForm').submit());

// Revoke moderator confirm
document.querySelectorAll('.cs-revoke-form').forEach(form => {
    form.addEventListener('submit', e => {
        const name = form.dataset.confirmName;
        if (!confirm(`Are you sure you want to revoke moderator privileges for ${name}?`)) {
            e.preventDefault();
        }
    });
});
