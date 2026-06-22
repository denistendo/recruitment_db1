function addQualificationRow() {
    const container = document.getElementById('qualifications-container');
    const noMsg = document.getElementById('no-quals-msg');
    if (noMsg) noMsg.remove();

    const row = document.createElement('div');
    row.className = 'qualification-row';
    row.innerHTML = `
        <div class="form-group-row">
            <div class="form-group">
                <label>Institution</label>
                <input type="text" class="qual-institution" placeholder="University name">
            </div>
            <div class="form-group">
                <label>Award</label>
                <input type="text" class="qual-award" placeholder="Degree / Diploma">
            </div>
        </div>
        <div class="form-group-row" style="align-items: end;">
            <div class="form-group">
                <label>Year Completed</label>
                <input type="number" class="qual-year" placeholder="2024" min="1900" max="2099">
            </div>
            <div class="form-group">
                <button class="btn btn-sm btn-danger" onclick="this.closest('.qualification-row').remove()">
                    <i class="bi bi-trash"></i> Remove
                </button>
            </div>
        </div>
    `;
    container.appendChild(row);
}

function saveQualifications() {
    const rows = document.querySelectorAll('.qualification-row');
    const qualifications = [];
    rows.forEach(row => {
        const institution = row.querySelector('.qual-institution').value.trim();
        const award = row.querySelector('.qual-award').value.trim();
        const year = row.querySelector('.qual-year').value.trim();
        if (institution || award) {
            qualifications.push({
                institution: institution,
                award: award,
                year_completed: year ? parseInt(year) : null
            });
        }
    });

    fetch('/api/qualifications/save/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
        body: JSON.stringify({ qualifications: qualifications })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            showToast(data.message, 'success');
        } else {
            showToast(data.message || 'Error saving qualifications', 'error');
        }
    })
    .catch(() => showToast('Network error', 'error'));
}

function saveSkills() {
    const checkboxes = document.querySelectorAll('.skill-checkbox:checked');
    const skills = [];
    checkboxes.forEach(cb => skills.push(parseInt(cb.value)));

    fetch('/api/skills/save/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
        body: JSON.stringify({ skills: skills })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            showToast(data.message, 'success');
        } else {
            showToast(data.message || 'Error saving skills', 'error');
        }
    })
    .catch(() => showToast('Network error', 'error'));
}

function getCSRFToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let c of cookies) {
        c = c.trim();
        if (c.startsWith(name + '=')) return decodeURIComponent(c.substring(name.length + 1));
    }
    return '';
}
