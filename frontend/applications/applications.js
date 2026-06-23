let applicationModalInstance = null;

function getApplicationModal() {
    const el = document.getElementById('application-modal');
    if (!applicationModalInstance) {
        applicationModalInstance = new bootstrap.Modal(el);
    }
    return applicationModalInstance;
}

function openCreateApplicationModal() {
    const form = document.getElementById('create-application-form');
    form.reset();
    delete form.dataset.editId;

    document.querySelector('#application-modal .modal-title').textContent = 'Add New Application';
    document.querySelector('#application-modal .btn-success').textContent = 'Save Application';

    document.getElementById('application-date').value = new Date().toISOString().split('T')[0];

    getApplicationModal().show();
}

function openEditApplicationModal(applicationId, applicantId, jobId, applicationDate, status) {
    const form = document.getElementById('create-application-form');
    form.reset();
    form.dataset.editId = applicationId;

    document.querySelector('#application-modal .modal-title').textContent = 'Edit Application';
    document.querySelector('#application-modal .btn-success').textContent = 'Update Application';

    document.getElementById('application-applicant').value = applicantId;
    document.getElementById('application-job').value = jobId;
    document.getElementById('application-date').value = applicationDate && applicationDate !== 'None' ? applicationDate : '';
    document.getElementById('application-status').value = status;

    getApplicationModal().show();
}

async function submitApplicationForm(event) {
    event.preventDefault();
    const form = document.getElementById('create-application-form');
    const editId = form.dataset.editId;

    const applicantId = document.getElementById('application-applicant').value;
    const jobId = document.getElementById('application-job').value;
    const applicationDate = document.getElementById('application-date').value;
    const status = document.getElementById('application-status').value;

    const payload = {
        applicant_id: applicantId,
        job_id: jobId,
        application_date: applicationDate || null,
        status: status || 'Pending'
    };

    const url = editId ? `/api/applications/update/${editId}/` : '/api/applications/create/';
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
            getApplicationModal().hide();
            form.reset();
            delete form.dataset.editId;
            refreshApplicationsTable();
        } else {
            showToast(result.message || 'Error occurred.', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
}

async function deleteApplication(applicationId) {
    if (!confirm('Are you sure you want to delete this application?')) return;

    try {
        const response = await fetch(`/api/applications/delete/${applicationId}/`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (response.ok) {
            showToast(result.message, 'success');
            const row = document.getElementById(`application-row-${applicationId}`);
            if (row) {
                row.remove();
            }
            checkEmptyStates();
        } else {
            showToast(result.message || 'Failed to delete application.', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
}

function formatDate(dateStr) {
    if (!dateStr || dateStr === 'None') return '';
    const parts = dateStr.split('-');
    if (parts.length !== 3) return dateStr;
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
}

async function refreshApplicationsTable() {
    try {
        const response = await fetch('/api/applications/');
        const result = await response.json();

        if (response.ok && result.applications) {
            const tbody = document.getElementById('applications-table-body');
            tbody.innerHTML = '';

            if (result.applications.length === 0) {
                tbody.innerHTML = `
                    <tr id="applications-empty-row">
                        <td colspan="6" class="text-center text-muted py-5">
                            <i class="bi bi-inbox" style="font-size: 2.5rem;"></i>
                            <p class="mt-2 mb-0 fw-medium">No applications found</p>
                            <small>Applications submitted by applicants will appear here.</small>
                        </td>
                    </tr>`;
                return;
            }

            result.applications.forEach(app => {
                const tr = document.createElement('tr');
                tr.id = `application-row-${app.application_id}`;
                const escapedApplicant = app.applicant_name.replace(/'/g, "\\'");
                const escapedJob = app.job_title.replace(/'/g, "\\'");

                const statusLower = app.status.toLowerCase();
                let badgeClass = 'bg-secondary';
                if (statusLower === 'accepted') badgeClass = 'bg-success';
                else if (statusLower === 'rejected') badgeClass = 'bg-danger';
                else if (statusLower === 'pending') badgeClass = 'bg-warning text-dark';
                else if (statusLower === 'interviewed') badgeClass = 'bg-info text-dark';
                else if (statusLower === 'not interviewed') badgeClass = 'bg-dark';

                tr.innerHTML = `
                    <td class="fw-semibold">${app.application_id}</td>
                    <td class="applicant-name-cell"><strong>${app.applicant_name}</strong></td>
                    <td>${app.job_title}</td>
                    <td>${formatDate(app.application_date) || '-'}</td>
                    <td><span class="badge ${badgeClass}">${app.status}</span></td>
                    <td class="text-center">
                        <div class="btn-group btn-group-sm" role="group">
                            <button class="btn btn-outline-primary" onclick="openEditApplicationModal(${app.application_id}, ${app.applicant_id}, ${app.job_id}, '${app.application_date}', '${app.status}')" title="Edit">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="deleteApplication(${app.application_id})" title="Delete">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error('Error reloading applications list:', error);
    }
}

function filterApplications() {
    const query = document.getElementById('search-applications').value.toLowerCase();
    const rows = document.querySelectorAll('#applications-table-body tr');

    rows.forEach(row => {
        if (row.id === 'applications-empty-row') return;
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
    });
}

function checkEmptyStates() {
    const appRows = document.querySelectorAll('#applications-table-body tr');
    if (appRows.length === 0 || (appRows.length === 1 && appRows[0].id === 'applications-empty-row')) {
        refreshApplicationsTable();
    }
}
