function getJobModal() {
    var el = document.getElementById('job-modal');
    if (!el) return null;
    return new bootstrap.Modal(el);
}

function openCreateJobModal() {
    var modal = getJobModal();
    if (!modal) return;
    document.getElementById('create-job-form').reset();
    document.getElementById('job-id').value = '';
    document.querySelector('#job-modal .modal-title').innerHTML = '<i class="bi bi-briefcase me-2"></i>Post New Job Vacancy';
    modal.show();
}

function openEditJobModal(jobId, title, description, departmentId, postedDate, closingDate) {
    var modal = getJobModal();
    if (!modal) return;
    document.getElementById('job-id').value = jobId;
    document.getElementById('job-title').value = title;
    document.getElementById('job-description').value = description;
    document.getElementById('job-department').value = departmentId;
    document.getElementById('job-posted-date').value = postedDate;
    document.getElementById('job-closing-date').value = closingDate;
    document.querySelector('#job-modal .modal-title').innerHTML = '<i class="bi bi-pencil me-2"></i>Edit Job Vacancy';
    modal.show();
}

function submitJobForm(event) {
    event.preventDefault();
    var id = document.getElementById('job-id').value;
    var data = {
        title: document.getElementById('job-title').value,
        description: document.getElementById('job-description').value,
        department: document.getElementById('job-department').value,
        posted_date: document.getElementById('job-posted-date').value,
        closing_date: document.getElementById('job-closing-date').value
    };
    var url = id ? '/api/jobs/update/' + id + '/' : '/api/jobs/create/';
    var method = id ? 'PUT' : 'POST';

    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify(data)
    })
    .then(function (response) { return response.json(); })
    .then(function (result) {
        if (result.status === 'success') {
            var modal = getJobModal();
            if (modal) modal.hide();
            showToast('Job saved successfully.', 'success');
            location.reload();
        } else {
            showToast(result.message || 'Error saving job.', 'error');
        }
    })
    .catch(function () {
        showToast('Error saving job.', 'error');
    });
}

function deleteJob(jobId) {
    if (!confirm('Are you sure you want to delete this job posting?')) return;
    fetch('/api/jobs/delete/' + jobId + '/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(function (response) { return response.json(); })
    .then(function (result) {
        if (result.status === 'success') {
            showToast('Job deleted.', 'success');
            var row = document.getElementById('job-row-' + jobId);
            if (row) row.remove();
        } else {
            showToast(result.message || 'Error deleting job.', 'error');
        }
    })
    .catch(function () {
        showToast('Error deleting job.', 'error');
    });
}

function filterJobs() {
    var input = document.getElementById('search-jobs');
    if (!input) return;
    var query = input.value.toLowerCase();
    var rows = document.querySelectorAll('#jobs-table tbody tr');
    rows.forEach(function (row) {
        if (row.id === 'jobs-empty-row') return;
        var text = row.textContent.toLowerCase();
        row.style.display = text.indexOf(query) > -1 ? '' : 'none';
    });
}
