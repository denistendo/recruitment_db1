let jobModalInstance = null;

function getJobModal() {
    const el = document.getElementById('job-modal');
    if (!jobModalInstance) {
        jobModalInstance = new bootstrap.Modal(el);
    }
    return jobModalInstance;
}

function openCreateJobModal() {
    const form = document.getElementById('create-job-form');
    form.reset();
    delete form.dataset.editId;

    document.querySelector('#job-modal .modal-title').textContent = 'Post New Job Vacancy';
    document.querySelector('#job-modal .btn-success').textContent = 'Post Job';

    getJobModal().show();
}

function openEditJobModal(jobId, title, description, departmentId, postedDate, closingDate) {
    const form = document.getElementById('create-job-form');
    form.reset();
    form.dataset.editId = jobId;

    document.querySelector('#job-modal .modal-title').textContent = 'Edit Job Posting';
    document.querySelector('#job-modal .btn-success').textContent = 'Update Job';

    document.getElementById('job-title').value = title;
    document.getElementById('job-description').value = description;
    document.getElementById('job-department').value = departmentId;

    document.getElementById('job-posted-date').value = postedDate && postedDate !== 'None' ? postedDate : '';
    document.getElementById('job-closing-date').value = closingDate && closingDate !== 'None' ? closingDate : '';

    getJobModal().show();
}

async function submitJobForm(event) {
    event.preventDefault();
    const form = document.getElementById('create-job-form');
    const editId = form.dataset.editId;

    const title = document.getElementById('job-title').value;
    const description = document.getElementById('job-description').value;
    const department = document.getElementById('job-department').value;
    const postedDate = document.getElementById('job-posted-date').value;
    const closingDate = document.getElementById('job-closing-date').value;

    const payload = {
        title: title,
        description: description,
        department: department,
        posted_date: postedDate || null,
        closing_date: closingDate || null
    };

    const url = editId ? `/api/jobs/update/${editId}/` : '/api/jobs/create/';
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
            getJobModal().hide();
            form.reset();
            delete form.dataset.editId;
            refreshJobsTable();
        } else {
            showToast(result.message || 'Error occurred.', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
}

async function deleteJob(jobId) {
    if (!confirm('Are you sure you want to delete this job vacancy?')) return;

    try {
        const response = await fetch(`/api/jobs/delete/${jobId}/`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (response.ok) {
            showToast(result.message, 'success');
            const row = document.getElementById(`job-row-${jobId}`);
            if (row) {
                row.remove();
            }
            checkEmptyStates();
        } else {
            showToast(result.message || 'Failed to delete job.', 'error');
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

async function refreshJobsTable() {
    try {
        const response = await fetch('/api/jobs/');
        const result = await response.json();

        if (response.ok && result.jobs) {
            const tbody = document.getElementById('jobs-table-body');
            tbody.innerHTML = '';

            if (result.jobs.length === 0) {
                tbody.innerHTML = `
                    <tr id="jobs-empty-row">
                        <td colspan="6" class="text-center text-muted py-5">
                            <i class="bi bi-inbox" style="font-size: 2.5rem;"></i>
                            <p class="mt-2 mb-0 fw-medium">No job postings found</p>
                            <small>Create a new job posting to get started.</small>
                        </td>
                    </tr>`;
                return;
            }

            result.jobs.forEach(job => {
                const tr = document.createElement('tr');
                tr.id = `job-row-${job.job_id}`;
                const escapedTitle = job.title.replace(/'/g, "\\'");
                const escapedDesc = job.description ? job.description.replace(/'/g, "\\'") : '';
                const deptId = job.department_id || '';

                tr.innerHTML = `
                    <td class="fw-semibold">${job.job_id}</td>
                    <td class="job-title-cell"><strong>${job.title}</strong></td>
                    <td>${job.department_name}</td>
                    <td>${formatDate(job.posted_date) || '-'}</td>
                    <td>${formatDate(job.closing_date) || '-'}</td>
                    <td class="text-center">
                        <div class="btn-group btn-group-sm" role="group">
                            <button class="btn btn-outline-primary" onclick="openEditJobModal(${job.job_id}, '${escapedTitle}', '${escapedDesc}', '${deptId}', '${job.posted_date}', '${job.closing_date}')" title="Edit">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="deleteJob(${job.job_id})" title="Delete">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error('Error reloading jobs list:', error);
    }
}

function filterJobs() {
    const query = document.getElementById('search-jobs').value.toLowerCase();
    const rows = document.querySelectorAll('#jobs-table-body tr');

    rows.forEach(row => {
        if (row.id === 'jobs-empty-row') return;
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
    });
}

function checkEmptyStates() {
    const jobRows = document.querySelectorAll('#jobs-table-body tr');
    if (jobRows.length === 0 || (jobRows.length === 1 && jobRows[0].id === 'jobs-empty-row')) {
        refreshJobsTable();
    }
}
