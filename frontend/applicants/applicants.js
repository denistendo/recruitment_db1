function openCreateApplicantModal() {
    const form = document.getElementById('create-applicant-form');
    form.reset();
    delete form.dataset.editId;

    document.querySelector('#applicant-modal h3').textContent = 'Add New Applicant';
    document.querySelector('#applicant-modal .btn-success').textContent = 'Save Applicant';

    openModal('applicant-modal');
}

function openEditApplicantModal(applicantId, userId, dateOfBirth, gender, phoneNumber, address) {
    const form = document.getElementById('create-applicant-form');
    form.reset();
    form.dataset.editId = applicantId;

    document.querySelector('#applicant-modal h3').textContent = 'Edit Applicant Profile';
    document.querySelector('#applicant-modal .btn-success').textContent = 'Update Applicant';

    document.getElementById('applicant-user').value = userId;
    document.getElementById('applicant-dob').value = dateOfBirth && dateOfBirth !== 'None' ? dateOfBirth : '';
    document.getElementById('applicant-gender').value = gender;
    document.getElementById('applicant-phone').value = phoneNumber;
    document.getElementById('applicant-address').value = address;

    openModal('applicant-modal');
}

async function submitApplicantForm(event) {
    event.preventDefault();
    const form = document.getElementById('create-applicant-form');
    const editId = form.dataset.editId;

    const userId = document.getElementById('applicant-user').value;
    const dateOfBirth = document.getElementById('applicant-dob').value;
    const gender = document.getElementById('applicant-gender').value;
    const phoneNumber = document.getElementById('applicant-phone').value;
    const address = document.getElementById('applicant-address').value;

    const payload = {
        user_id: userId,
        date_of_birth: dateOfBirth || null,
        gender: gender || null,
        phone_number: phoneNumber || null,
        address: address || null
    };

    const url = editId ? `/api/applicants/update/${editId}/` : '/api/applicants/create/';
    const method = editId ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok) {
            showToast(result.message, 'success');
            closeModal('applicant-modal');
            form.reset();
            delete form.dataset.editId;
            refreshApplicantsTable();
        } else {
            showToast(result.message || 'Error occurred.', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
}

async function deleteApplicant(applicantId) {
    if (!confirm('Are you sure you want to delete this applicant profile?')) return;

    try {
        const response = await fetch(`/api/applicants/delete/${applicantId}/`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (response.ok) {
            showToast(result.message, 'success');
            const row = document.getElementById(`applicant-row-${applicantId}`);
            if (row) {
                row.remove();
            }
            checkEmptyStates();
        } else {
            showToast(result.message || 'Failed to delete applicant.', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
}

async function refreshApplicantsTable() {
    try {
        const response = await fetch('/api/applicants/');
        const result = await response.json();

        if (response.ok && result.applicants) {
            const tbody = document.getElementById('applicants-table-body');
            tbody.innerHTML = '';

            if (result.applicants.length === 0) {
                tbody.innerHTML = `
                    <tr id="applicants-empty-row">
                        <td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                            No applicant records found in the database.
                        </td>
                    </tr>`;
                return;
            }

            result.applicants.forEach(a => {
                const tr = document.createElement('tr');
                tr.id = `applicant-row-${a.applicant_id}`;
                const escapedName = a.full_name.replace(/'/g, "\\'");
                const escapedPhone = (a.phone_number || '').replace(/'/g, "\\'");
                const escapedAddress = (a.address || '').replace(/'/g, "\\'");
                const escapedGender = (a.gender || '').replace(/'/g, "\\'");

                tr.innerHTML = `
                    <td>${a.applicant_id}</td>
                    <td class="applicant-name-cell">${a.full_name}</td>
                    <td>${a.email}</td>
                    <td>${a.date_of_birth || '-'}</td>
                    <td>${a.gender || '-'}</td>
                    <td>${a.phone_number || '-'}</td>
                    <td style="text-align: center;">
                        <button class="btn-edit" onclick="openEditApplicantModal(${a.applicant_id}, ${a.user_id}, '${a.date_of_birth}', '${escapedGender}', '${escapedPhone}', '${escapedAddress}')">Edit</button>
                        <button class="btn-danger" onclick="deleteApplicant(${a.applicant_id})">Delete</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error('Error reloading applicants list:', error);
    }
}

function filterApplicants() {
    const query = document.getElementById('search-applicants').value.toLowerCase();
    const rows = document.querySelectorAll('#applicants-table-body tr');

    rows.forEach(row => {
        if (row.id === 'applicants-empty-row') return;
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
    });
}

function checkEmptyStates() {
    const applicantRows = document.querySelectorAll('#applicants-table-body tr');
    if (applicantRows.length === 0 || (applicantRows.length === 1 && applicantRows[0].id === 'applicants-empty-row')) {
        refreshApplicantsTable();
    }
}