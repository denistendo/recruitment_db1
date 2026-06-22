function toggleEditProfile() {
    document.getElementById('profile-display').style.display = 'none';
    document.getElementById('profile-edit').style.display = 'block';
    document.getElementById('edit-profile-btn').style.display = 'none';
}

function cancelEditProfile() {
    document.getElementById('profile-display').style.display = 'block';
    document.getElementById('profile-edit').style.display = 'none';
    document.getElementById('edit-profile-btn').style.display = 'inline-block';
}

function parseDateDDMMYYYY(value) {
    if (!value) return null;
    const parts = value.split('/');
    if (parts.length !== 3) return value;
    return `${parts[2]}-${parts[1]}-${parts[0]}`;
}

async function saveProfile() {
    const dobInput = document.getElementById('edit-dob').value;
    const data = {
        date_of_birth: parseDateDDMMYYYY(dobInput),
        gender: document.getElementById('edit-gender').value || null,
        phone_number: document.getElementById('edit-phone').value || null,
        address: document.getElementById('edit-address').value || null,
    };

    try {
        const response = await fetch('/api/profile/update/', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (response.ok) {
            showToast(result.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(result.message || 'Error saving profile.', 'error');
        }
    } catch (err) {
        showToast('Network error: ' + err.message, 'error');
    }
}

function openAddQualificationModal() {
    document.getElementById('qualification-form').reset();
    delete document.getElementById('qualification-form').dataset.editId;
    document.getElementById('qual-modal-title').textContent = 'Add Qualification';
    document.getElementById('qual-submit-btn').textContent = 'Add Qualification';
    openModal('qualification-modal');
}

function openEditQualificationModal(id, institution, award, year) {
    const form = document.getElementById('qualification-form');
    form.reset();
    form.dataset.editId = id;
    document.getElementById('qual-modal-title').textContent = 'Edit Qualification';
    document.getElementById('qual-submit-btn').textContent = 'Update Qualification';
    document.getElementById('qual-institution').value = institution;
    document.getElementById('qual-award').value = award;
    document.getElementById('qual-year').value = year && year !== 'None' ? year : '';
    openModal('qualification-modal');
}

async function submitQualificationForm(event) {
    event.preventDefault();
    const form = document.getElementById('qualification-form');
    const editId = form.dataset.editId;
    const institution = document.getElementById('qual-institution').value.trim();
    const award = document.getElementById('qual-award').value.trim();
    const year = document.getElementById('qual-year').value;

    const payload = {
        institution: institution,
        award: award,
        year_completed: year ? parseInt(year) : null
    };

    const url = editId ? `/api/qualifications/update/${editId}/` : '/api/qualifications/create/';
    const method = editId ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (response.ok) {
            showToast(result.message, 'success');
            closeModal('qualification-modal');
            form.reset();
            delete form.dataset.editId;
            reloadPage();
        } else {
            showToast(result.message || 'Error saving qualification.', 'error');
        }
    } catch (err) {
        showToast('Network error: ' + err.message, 'error');
    }
}

async function deleteQualification(id) {
    if (!confirm('Delete this qualification?')) return;
    try {
        const response = await fetch(`/api/qualifications/delete/${id}/`, { method: 'DELETE' });
        const result = await response.json();
        if (response.ok) {
            showToast(result.message, 'success');
            const row = document.getElementById(`qual-row-${id}`);
            if (row) row.remove();
            checkQualsEmpty();
        } else {
            showToast(result.message || 'Error deleting qualification.', 'error');
        }
    } catch (err) {
        showToast('Network error: ' + err.message, 'error');
    }
}

function checkQualsEmpty() {
    const rows = document.querySelectorAll('#qualifications-table tbody tr');
    const hasData = Array.from(rows).some(r => r.id !== 'quals-empty-row');
    if (!hasData) {
        const tbody = document.querySelector('#qualifications-table tbody');
        tbody.innerHTML = `<tr id="quals-empty-row"><td colspan="4" class="text-center text-muted py-4">No qualifications added yet.</td></tr>`;
    }
}

function openAddSkillModal() {
    document.getElementById('skill-form').reset();
    delete document.getElementById('skill-form').dataset.editId;
    document.getElementById('skill-modal-title').textContent = 'Add Skill';
    document.getElementById('skill-submit-btn').textContent = 'Add Skill';
    openModal('skill-modal');
}

function openEditSkillModal(applicantSkillId, skillId, skillName, proficiency) {
    const form = document.getElementById('skill-form');
    form.reset();
    form.dataset.editId = applicantSkillId;
    document.getElementById('skill-modal-title').textContent = 'Edit Skill';
    document.getElementById('skill-submit-btn').textContent = 'Update Skill';
    document.getElementById('skill-input').value = skillName;
    document.getElementById('skill-proficiency').value = proficiency;
    openModal('skill-modal');
}

async function submitSkillForm(event) {
    event.preventDefault();
    const form = document.getElementById('skill-form');
    const editId = form.dataset.editId;
    const skillName = document.getElementById('skill-input').value.trim();
    const proficiency = document.getElementById('skill-proficiency').value;

    if (!skillName) {
        showToast('Please enter or select a skill.', 'error');
        return;
    }

    const payload = { skill_name: skillName, proficiency_level: proficiency };

    const url = editId ? `/api/applicant-skills/update/${editId}/` : '/api/applicant-skills/create/';
    const method = editId ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (response.ok) {
            showToast(result.message, 'success');
            closeModal('skill-modal');
            form.reset();
            delete form.dataset.editId;
            reloadPage();
        } else {
            showToast(result.message || 'Error saving skill.', 'error');
        }
    } catch (err) {
        showToast('Network error: ' + err.message, 'error');
    }
}

async function deleteSkill(applicantSkillId) {
    if (!confirm('Remove this skill?')) return;
    try {
        const response = await fetch(`/api/applicant-skills/delete/${applicantSkillId}/`, { method: 'DELETE' });
        const result = await response.json();
        if (response.ok) {
            showToast(result.message, 'success');
            const row = document.getElementById(`skill-row-${applicantSkillId}`);
            if (row) row.remove();
            checkSkillsEmpty();
        } else {
            showToast(result.message || 'Error removing skill.', 'error');
        }
    } catch (err) {
        showToast('Network error: ' + err.message, 'error');
    }
}

function checkSkillsEmpty() {
    const rows = document.querySelectorAll('#skills-table tbody tr');
    const hasData = Array.from(rows).some(r => r.id !== 'skills-empty-row');
    if (!hasData) {
        const tbody = document.querySelector('#skills-table tbody');
        tbody.innerHTML = `<tr id="skills-empty-row"><td colspan="3" class="text-center text-muted py-4">No skills added yet.</td></tr>`;
    }
}

function reloadPage() {
    setTimeout(() => location.reload(), 500);
}