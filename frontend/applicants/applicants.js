function getApplicantModal() {
    const el = document.getElementById('applicant-modal');
    return bootstrap.Modal.getInstance(el) || new bootstrap.Modal(el);
}

function openCreateApplicantModal() {
    const form = document.getElementById('create-applicant-form');
    form.reset();
    delete form.dataset.editId;

    document.getElementById('applicant-modal-title').textContent = 'Add New Applicant';
    document.getElementById('applicant-submit-btn').textContent = 'Save Applicant';

    getApplicantModal().show();
}

function openEditApplicantModal(applicantId, userId, dateOfBirth, gender, phoneNumber, address) {
    const form = document.getElementById('create-applicant-form');
    form.reset();
    form.dataset.editId = applicantId;

    document.getElementById('applicant-modal-title').textContent = 'Edit Applicant Profile';
    document.getElementById('applicant-submit-btn').textContent = 'Update Applicant';

    document.getElementById('applicant-user').value = userId;
    document.getElementById('applicant-dob').value = dateOfBirth && dateOfBirth !== 'None' ? dateOfBirth : '';
    document.getElementById('applicant-gender').value = gender;
    document.getElementById('applicant-phone').value = phoneNumber;
    document.getElementById('applicant-address').value = address;

    getApplicantModal().show();
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
            getApplicantModal().hide();
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
            updateApplicantCount();
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
                        <td colspan="7" class="text-center text-muted py-5">
                            <i class="bi bi-inbox" style="font-size: 2.5rem;"></i>
                            <p class="mt-2 mb-0 fw-medium">No applicant records found</p>
                            <small>Click "Add Applicant" to create the first profile.</small>
                        </td>
                    </tr>`;
                return;
            }

            result.applicants.forEach(a => {
                const tr = document.createElement('tr');
                tr.id = `applicant-row-${a.applicant_id}`;
                const dob = a.date_of_birth && a.date_of_birth !== 'None' ? a.date_of_birth : '';
                const phone = (a.phone_number || '').replace(/'/g, "\\'");
                const address = (a.address || '').replace(/'/g, "\\'");
                const gender = (a.gender || '').replace(/'/g, "\\'");

                tr.innerHTML = `
                    <td class="fw-semibold">${a.applicant_id}</td>
                    <td class="applicant-name-cell">${a.full_name}</td>
                    <td>${a.email}</td>
                    <td>${dob || '-'}</td>
                    <td>${genderBadge(a.gender)}</td>
                    <td>${a.phone_number || '-'}</td>
                    <td class="text-center">
                        <div class="btn-group btn-group-sm" role="group">
                            <button class="btn btn-outline-primary" title="Edit" onclick="openEditApplicantModal(${a.applicant_id}, ${a.user_id}, '${dob}', '${gender}', '${phone}', '${address}')">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-outline-danger" title="Delete" onclick="deleteApplicant(${a.applicant_id})">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                `;
                tbody.appendChild(tr);
            });
            updateApplicantCount();
        }
    } catch (error) {
        console.error('Error reloading applicants list:', error);
    }
}

function genderBadge(gender) {
    if (!gender) return '<span class="text-muted">-</span>';
    const cls = gender === 'Male' ? 'primary' : gender === 'Female' ? 'danger' : 'secondary';
    return `<span class="badge bg-${cls} bg-opacity-10 text-${cls}">${gender}</span>`;
}

function updateApplicantCount() {
    const count = document.querySelectorAll('#applicants-table-body tr[id^="applicant-row-"]').length;
    const badge = document.getElementById('applicant-count');
    if (badge) badge.textContent = count + ' Total';
}

function filterApplicants() {
    const query = document.getElementById('search-applicants').value.toLowerCase();
    const rows = document.querySelectorAll('#applicants-table-body tr');
    let visible = 0;

    rows.forEach(row => {
        if (row.id === 'applicants-empty-row') return;
        const text = row.textContent.toLowerCase();
        const match = text.includes(query);
        row.style.display = match ? '' : 'none';
        if (match) visible++;
    });

    const emptyRow = document.querySelector('#applicants-table-body #applicants-empty-row');
    if (emptyRow) {
        emptyRow.style.display = visible === 0 ? '' : 'none';
    }
    updateApplicantCount();
}

function checkEmptyStates() {
    const applicantRows = document.querySelectorAll('#applicants-table-body tr');
    if (applicantRows.length === 0 || (applicantRows.length === 1 && applicantRows[0].id === 'applicants-empty-row')) {
        refreshApplicantsTable();
    }
}