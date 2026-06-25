function previewBanner(input) {
    const placeholder = document.getElementById('bannerPlaceholder');
    const img = document.getElementById('bannerImg');

    if (input.files && input.files[0] && placeholder && img) {
        const reader = new FileReader();
        reader.onload = (e) => {
            img.src = e.target.result;
            img.style.display = 'block';
            placeholder.style.display = 'none';
        }
        reader.readAsDataURL(input.files[0]);
    }
}

function previewMap(input) {
    const placeholder = document.getElementById('mapPlaceholder');
    const img = document.getElementById('mapImg');

    if (input.files && input.files[0] && placeholder && img) {
        const reader = new FileReader();
        reader.onload = (e) => {
            img.src = e.target.result;
            img.style.display = 'block';
            placeholder.style.display = 'none';
        }
        reader.readAsDataURL(input.files[0]);
    }
}

function updateName(val) {
    const previewName = document.getElementById('previewName');
    if (previewName) {
        previewName.textContent = val || "New Campus";
    }
}

function updateDesc(val) {
    const previewDesc = document.getElementById('previewDesc');
    if (previewDesc) {
        previewDesc.textContent = val || "Description will appear here...";
    }
}
