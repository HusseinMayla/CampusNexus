document.addEventListener("DOMContentLoaded", () => {
    // ── Modal elements ────────────────────────────────────────────────────────
    const shareModal = document.getElementById('shareModal');       // modal for uploading a resource file
    const requestModal = document.getElementById('requestModal');   // modal for posting a resource request
    const fFile = document.getElementById('f-file');               // hidden file input
    const fileNameDisplay = document.getElementById('fileNameDisplay');  // shows selected filename
    const fileDropLabel = document.getElementById('fileDropLabel');      // "click to upload" label
    const fileDrop = document.getElementById('fileDrop');                // clickable file drop area

    // ── Share modal: open and close ───────────────────────────────────────────

    // Opens the share modal and focuses the course code input
    function openShare() {
        shareModal.classList.add('open');
        document.getElementById('f-code').focus();
    }

    // Closes the share modal and resets all its fields back to empty
    function closeShare() {
        shareModal.classList.remove('open');
        document.getElementById('f-code').value = '';
        fFile.value = '';
        fileNameDisplay.classList.add('res-hidden');
        fileDropLabel.classList.remove('res-hidden');
        fileDrop.classList.remove('has-file');
        document.getElementById('f-share-chapters').value = '';
    }

    // ── Request modal: open and close ─────────────────────────────────────────

    // Opens the request modal and focuses the email input
    function openRequest() {
        requestModal.classList.add('open');
        document.getElementById('r-email').focus();
    }

    // Closes the request modal and resets all its fields
    function closeRequest() {
        requestModal.classList.remove('open');
        document.getElementById('r-email').value = '';
        document.getElementById('r-code').value = '';
        document.getElementById('f-request-chapters').value = '';
    }

    // ── Button wiring ─────────────────────────────────────────────────────────

    document.getElementById('btnOpenShare').addEventListener('click', openShare);
    document.getElementById('btnOpenRequest').addEventListener('click', openRequest);

    // "Share" button shown when the list is empty
    const btnEmptyShare = document.getElementById('btnEmptyShare');
    if (btnEmptyShare) btnEmptyShare.addEventListener('click', openShare);

    // "Request" button shown when the list is empty
    const btnEmptyRequest = document.getElementById('btnEmptyRequest');
    if (btnEmptyRequest) btnEmptyRequest.addEventListener('click', openRequest);

    // Clicking the compose bar also opens the share modal
    const composeBar = document.querySelector('.compose-bar');
    if (composeBar) composeBar.addEventListener('click', openShare);

    // Close modals via close button or clicking the backdrop
    document.getElementById('shareCloseBtn').addEventListener('click', closeShare);
    shareModal.addEventListener('click', e => {
        if (e.target === shareModal) closeShare();  // click outside modal content closes it
    });

    document.getElementById('requestCloseBtn').addEventListener('click', closeRequest);
    requestModal.addEventListener('click', e => {
        if (e.target === requestModal) closeRequest();
    });

    // ── File input interaction ────────────────────────────────────────────────

    // Clicking the drop area triggers the hidden file input
    fileDrop.addEventListener('click', () => fFile.click());

    // When a file is selected, show its name and hide the "click to upload" label
    fFile.addEventListener('change', () => {
        const file = fFile.files[0];
        if (file) {
            fileNameDisplay.textContent = file.name;
            fileNameDisplay.classList.remove('res-hidden');
            fileDropLabel.classList.add('res-hidden');
            fileDrop.classList.add('has-file');     // adds visual style to show a file is ready
        } else {
            fileNameDisplay.classList.add('res-hidden');
            fileDropLabel.classList.remove('res-hidden');
            fileDrop.classList.remove('has-file');
        }
    });
});
