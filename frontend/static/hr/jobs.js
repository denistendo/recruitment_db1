function getJobModal() {
    var el = document.getElementById('job-modal');
    if (!el) return null;
    var modal = new bootstrap.Modal(el);
    return modal;
}

function openCreateJobModal() {
    var modal = getJobModal();
    if (!modal) return;
    document.getElementById('job-form').reset();
    document.getElementById('job-id').value = '';
    document.getElementById('job-modal-title').textContent = 'Create Job';
    modal.show();
}

function openEditJobModal(jobId, title, description, departmentId, postedDate, closingDate) {
    var modal = getJobModal();
    if (!modal) return;
    document.getElementById('job-id').value = jobId;
    document.getElementById('id_title').value = title;
    document.getElementById('id_description').value = description;
    document.getElementById('id_department').value = departmentId;
    document.getElementById('id_posted_date').value = postedDate;
    document.getElementById('id_closing_date').value = closingDate;
    document.getElementById('job-modal-title').textContent = 'Edit Job';
    modal.show();
}

function submitJobForm(event) {
    event.preventDefault();
    var id = document.getElementById('job-id').value;
    var data = {
        title: document.getElementById('id_title').value,
        description: document.getElementById('id_description').value,
        department: document.getElementById('id_department').value,
        posted_date: document.getElementById('id_posted_date').value,
        closing_date: document.getElementById('id_closing_date').value
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
        if (result.success) {
            var modal = getJobModal();
            if (modal) modal.hide();
            showToast('Job saved successfully.', 'success');
            refreshJobsTable();
        } else {
            showToast(result.error || 'Error saving job.', 'error');
        }
    })
    .catch(function () {
        showToast('Error saving job.', 'error');
    });
}

function deleteJob(jobId) {
    if (!confirm('Are you sure you want to delete this job?')) return;
    fetch('/api/jobs/delete/' + jobId + '/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(function (response) { return response.json(); })
    .then(function (result) {
        if (result.success) {
            showToast('Job deleted.', 'success');
            refreshJobsTable();
        } else {
            showToast('Error deleting job.', 'error');
        }
    })
    .catch(function () {
        showToast('Error deleting job.', 'error');
    });
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    var d = new Date(dateStr);
    var day = ('0' + d.getDate()).slice(-2);
    var month = ('0' + (d.getMonth() + 1)).slice(-2);
    var year = d.getFullYear();
    return day + '/' + month + '/' + year;
}

function refreshJobsTable() {
    var tbody = document.querySelector('#jobs-table tbody');
    if (!tbody) return;
    fetch('/api/jobs/')
    .then(function (response) { return response.json(); })
    .then(function (data) {
        tbody.innerHTML = '';
        if (!data.jobs || data.jobs.length === 0) {
            checkEmptyStates();
            return;
        }
        data.jobs.forEach(function (job) {
            var tr = document.createElement('tr');
            tr.innerHTML =
                '<td class="job-title-cell">' + job.title + '</td>' +
                '<td>' + (job.department_name || '') + '</td>' +
                '<td>' + formatDate(job.posted_date) + '</td>' +
                '<td>' + formatDate(job.closing_date) + '</td>' +
                '<td>' +
                    '<button class="btn btn-sm btn-outline-primary me-1" onclick="openEditJobModal(' +
                        job.id + ', \'' + job.title.replace(/'/g, "\\'") + '\', \'' + (job.description || '').replace(/'/g, "\\'") + '\', ' + (job.department_id || '') + ', \'' + (job.posted_date || '') + '\', \'' + (job.closing_date || '') + '\')">Edit</button>' +
                    '<button class="btn btn-sm btn-outline-danger" onclick="deleteJob(' + job.id + ')">Delete</button>' +
                '</td>';
            tbody.appendChild(tr);
        });
    })
    .catch(function () {
        showToast('Error loading jobs.', 'error');
    });
}

function filterJobs() {
    var input = document.getElementById('job-search');
    if (!input) return;
    var query = input.value.toLowerCase();
    var rows = document.querySelectorAll('#jobs-table tbody tr');
    rows.forEach(function (row) {
        if (row.classList.contains('empty-row')) return;
        var text = row.textContent.toLowerCase();
        row.style.display = text.indexOf(query) > -1 ? '' : 'none';
    });
}

function checkEmptyStates() {
    var tbody = document.querySelector('#jobs-table tbody');
    if (!tbody) return;
    if (tbody.querySelectorAll('tr').length === 0) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="5" style="text-align:center;">No jobs found.</td></tr>';
    }
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
