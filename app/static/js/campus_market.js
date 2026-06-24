document.addEventListener("DOMContentLoaded", () => {
    const modalOverlay = document.getElementById('modalOverlay');
    const fRoleInput = document.getElementById('f-role');
    const fMethodInput = document.getElementById('f-method');
    
    // Modal controls
    function openModal() {
        modalOverlay.classList.add('open');
        document.getElementById('f-name').focus();
    }
    
    function closeModal() {
        modalOverlay.classList.remove('open');
        document.getElementById('f-name').value = '';
        document.getElementById('f-email').value = '';
        document.getElementById('f-courses').value = '';
        fRoleInput.value = '';
        fMethodInput.value = '';
        document.querySelectorAll('.choice-btn').forEach(btn => btn.classList.remove('sel'));
    }
    
    document.getElementById('btnOpenModal').addEventListener('click', openModal);
    const btnEmptyModal = document.getElementById('btnEmptyModal');
    if (btnEmptyModal) {
        btnEmptyModal.addEventListener('click', openModal);
    }
    const composeBar = document.querySelector('.compose-bar');
    if (composeBar) {
        composeBar.addEventListener('click', openModal);
    }
    
    document.getElementById('modalCloseBtn').addEventListener('click', closeModal);
    modalOverlay.addEventListener('click', e => {
        if (e.target === modalOverlay) {
            closeModal();
        }
    });

    // Choice buttons selection
    const choiceButtons = document.querySelectorAll('.choice-btn');
    choiceButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const group = btn.parentElement;
            const groupBtns = group.querySelectorAll('.choice-btn');
            groupBtns.forEach(b => {
                b.classList.remove('sel');
            });
            btn.classList.add('sel');
            
            const val = btn.getAttribute('data-val');
            const type = group.getAttribute('data-group');
            if (type === 'role') {
                fRoleInput.value = val;
            } else if (type === 'method') {
                fMethodInput.value = val;
            }
        });
    });

    // Client-side Filters
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const filterValue = btn.dataset.filter;
            document.querySelectorAll('.post-card').forEach(card => {
                if (filterValue === 'all' || card.dataset.role === filterValue) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });
});
