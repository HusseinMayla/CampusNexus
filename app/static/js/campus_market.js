document.addEventListener("DOMContentLoaded", () => {
    // ── Modal elements ────────────────────────────────────────────────────────
    const modalOverlay = document.getElementById('modalOverlay');   // modal for creating a tutor/student post
    const fRoleInput = document.getElementById('f-role');           // hidden input storing selected role (tutor/student)
    const fMethodInput = document.getElementById('f-method');       // hidden input storing selected method (online/in-person/etc)

    // ── Modal open and close ──────────────────────────────────────────────────

    // Opens the post creation modal and focuses the name input
    function openModal() {
        modalOverlay.classList.add('open');
        document.getElementById('f-name').focus();
    }

    // Closes the modal and resets all fields and button selections
    function closeModal() {
        modalOverlay.classList.remove('open');
        document.getElementById('f-name').value = '';
        document.getElementById('f-email').value = '';
        document.getElementById('f-courses').value = '';
        fRoleInput.value = '';
        fMethodInput.value = '';
        document.querySelectorAll('.choice-btn').forEach(btn => btn.classList.remove('sel'));
    }

    // ── Button wiring ─────────────────────────────────────────────────────────

    document.getElementById('btnOpenModal').addEventListener('click', openModal);

    // "Post" button shown when the list is empty
    const btnEmptyModal = document.getElementById('btnEmptyModal');
    if (btnEmptyModal) {
        btnEmptyModal.addEventListener('click', openModal);
    }

    // Clicking the compose bar also opens the modal
    const composeBar = document.querySelector('.compose-bar');
    if (composeBar) {
        composeBar.addEventListener('click', openModal);
    }

    // Close modal via close button or clicking the backdrop
    document.getElementById('modalCloseBtn').addEventListener('click', closeModal);
    modalOverlay.addEventListener('click', e => {
        if (e.target === modalOverlay) {
            closeModal();   // click outside modal content closes it
        }
    });

    // ── Choice button selection (role and method) ─────────────────────────────
    // Choice buttons are styled radio-like buttons for selecting role (tutor/student)
    // and method (online/in-person/hybrid/no-preference).
    // Clicking one deselects the others in the same group and updates the hidden input
    const choiceButtons = document.querySelectorAll('.choice-btn');
    choiceButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const group = btn.parentElement;
            const groupBtns = group.querySelectorAll('.choice-btn');
            groupBtns.forEach(b => {
                b.classList.remove('sel');  // deselect all in group
            });
            btn.classList.add('sel');       // select clicked one

            const val = btn.getAttribute('data-val');
            const type = group.getAttribute('data-group');
            if (type === 'role') {
                fRoleInput.value = val;     // set hidden role input (submitted with form)
            } else if (type === 'method') {
                fMethodInput.value = val;   // set hidden method input
            }
        });
    });

    // ── Client-side filters ───────────────────────────────────────────────────
    // Filters the visible post cards by role (all / tutor / student) without a page reload.
    // Shows/hides cards by toggling display style based on their data-role attribute
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const filterValue = btn.dataset.filter;
            document.querySelectorAll('.post-card').forEach(card => {
                if (filterValue === 'all' || card.dataset.role === filterValue) {
                    card.style.display = '';        // show
                } else {
                    card.style.display = 'none';    // hide
                }
            });
        });
    });
});
