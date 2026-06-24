document.addEventListener("DOMContentLoaded", () => {
    const shareModal = document.getElementById('shareModal');
    const requestModal = document.getElementById('requestModal');
    const fFile = document.getElementById('f-file');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const fileDropLabel = document.getElementById('fileDropLabel');
    const fileDrop = document.getElementById('fileDrop');

    // Share modal controls
    function openShare() {
        shareModal.classList.add('open');
        document.getElementById('f-code').focus();
    }
    
    function closeShare() {
        shareModal.classList.remove('open');
        document.getElementById('f-code').value = '';
        fFile.value = '';
        fileNameDisplay.classList.add('res-hidden');
        fileDropLabel.classList.remove('res-hidden');
        fileDrop.classList.remove('has-file');
        document.getElementById('f-share-chapters').value = '';
    }

    // Request modal controls
    function openRequest() {
        requestModal.classList.add('open');
        document.getElementById('r-email').focus();
    }

    function closeRequest() {
        requestModal.classList.remove('open');
        document.getElementById('r-email').value = '';
        document.getElementById('r-code').value = '';
        document.getElementById('f-request-chapters').value = '';
    }

    // Event wiring
    document.getElementById('btnOpenShare').addEventListener('click', openShare);
    document.getElementById('btnOpenRequest').addEventListener('click', openRequest);

    const btnEmptyShare = document.getElementById('btnEmptyShare');
    if (btnEmptyShare) btnEmptyShare.addEventListener('click', openShare);

    const btnEmptyRequest = document.getElementById('btnEmptyRequest');
    if (btnEmptyRequest) btnEmptyRequest.addEventListener('click', openRequest);

    const composeBar = document.querySelector('.compose-bar');
    if (composeBar) composeBar.addEventListener('click', openShare);

    document.getElementById('shareCloseBtn').addEventListener('click', closeShare);
    shareModal.addEventListener('click', e => {
        if (e.target === shareModal) closeShare();
    });

    document.getElementById('requestCloseBtn').addEventListener('click', closeRequest);
    requestModal.addEventListener('click', e => {
        if (e.target === requestModal) closeRequest();
    });

    // File input interaction
    fileDrop.addEventListener('click', () => fFile.click());
    fFile.addEventListener('change', () => {
        const file = fFile.files[0];
        if (file) {
            fileNameDisplay.textContent = file.name;
            fileNameDisplay.classList.remove('res-hidden');
            fileDropLabel.classList.add('res-hidden');
            fileDrop.classList.add('has-file');
        } else {
            fileNameDisplay.classList.add('res-hidden');
            fileDropLabel.classList.remove('res-hidden');
            fileDrop.classList.remove('has-file');
        }
    });
});
