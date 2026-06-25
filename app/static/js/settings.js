document.addEventListener('DOMContentLoaded', () => {
    const deleteOverlay = document.getElementById('deleteConfirmOverlay');
    const deleteBox = deleteOverlay ? deleteOverlay.querySelector('.base-confirm-box') : null;
    const triggerDeleteBtn = document.getElementById('triggerDeleteBtn');
    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    const deleteAccountForm = document.getElementById('deleteAccountForm');

    if (!deleteOverlay || !deleteBox) return;

    function openDeleteModal() {
        deleteOverlay.classList.add('open');
        // Allow display change to take effect before setting opacity
        requestAnimationFrame(() => {
            deleteOverlay.style.opacity = '1';
            deleteBox.style.transform = 'scale(1)';
        });
    }

    function closeDeleteModal() {
        deleteOverlay.style.opacity = '0';
        deleteBox.style.transform = 'scale(0.95)';
        // Wait for transition to complete before removing open class
        setTimeout(() => {
            deleteOverlay.classList.remove('open');
        }, 200);
    }

    if (triggerDeleteBtn) {
        triggerDeleteBtn.addEventListener('click', openDeleteModal);
    }

    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', closeDeleteModal);
    }

    if (confirmDeleteBtn && deleteAccountForm) {
        confirmDeleteBtn.addEventListener('click', () => {
            deleteAccountForm.submit();
        });
    }

    // Close when clicking outside of modal box
    deleteOverlay.addEventListener('click', (e) => {
        if (e.target === deleteOverlay) {
            closeDeleteModal();
        }
    });
});
