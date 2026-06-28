function getApplicationModal() {
    var el = document.getElementById('application-modal');
    if (!el) return null;
    var modal = new bootstrap.Modal(el);
    return modal;
}

function openCreateApplicationModal() {
    var modal = getApplicationModal();
    if (!modal) return;
    document.getElementById('application-form').reset();
    document.getElementById('application-id').value = '';
    document.getElementById('application-modal-title').textContent = 'Create Application';
    var today = new Date().toISOString().split('T')[0];
    var dateInput = document.getElementById('id_application_date');
    if (dateInput) dateInput.value = today;
    modal.show();
}

function openEditApplicationModal(applicationId, applicantId, jobId, applicationDate, status) {
    var modal = getApplicationModal();
    if (!modal) return;
    document.getElementById('application-id').value = applicationId;
    document.getElementById('id_applicant').value = applicantId;
    document.getElementById('id_job').value = jobId;
    document.getElementById('id_application_date').value = applicationDate;
    document.getElementById('id_status').value = status;
    document.getElementById('application-modal-title').textContent = 'Edit Application';
    modal.show();
}

function submitApplicationForm(event) {
    event.preventDefault();
    var id = document.getElementById('application-id').value;
    var data = {
        applicant: document.getElementById('id_applicant').value,
        job: document.getElementById('id_job').value,
        application_date: document.getElementById('id_application_date').value,
        status: document.getElementById('id_status').value
    };
    var url = id ? '/api/applications/update/' + id + '/' : '/api/applications/create/';
    var method = id ? 'PUT' : 'POST';

    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify(data)
    })
    .then(function (response) { return response.json(); })
    .then(function (result) {
        if (result.success) {
            var modal = getApplicationModal();
            if (modal) modal.hide();
            showToast('Application saved successfully.', 'success');
            refreshApplicationsTable();
        } else {
            showToast(result.error || 'Error saving application.', 'error');
        }
    })
    .catch(function () {
        showToast('Error saving application.', 'error');
    });
}

function deleteApplication(applicationId) {
    if (!confirm('Are you sure you want to delete this application?')) return;
    fetch('/api/applications/delete/' + applicationId + '/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(function (response) { return response.json(); })
    .then(function (result) {
        if (result.success) {
            showToast('Application deleted.', 'success');
            refreshApplicationsTable();
        } else {
            showToast('Error deleting application.', 'error');
        }
    })
    .catch(function () {
        showToast('Error deleting application.', 'error');
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

function refreshApplicationsTable() {
    var tbody = document.querySelector('#applications-table tbody');
    if (!tbody) return;
    fetch('/api/applications/')
    .then(function (response) { return response.json(); })
    .then(function (data) {
        tbody.innerHTML = '';
        if (!data.applications || data.applications.length === 0) {
            checkEmptyStates();
            return;
        }
        data.applications.forEach(function (app) {
            var tr = document.createElement('tr');
            tr.innerHTML =
                '<td>' + app.applicant_name + '</td>' +
                '<td>' + app.job_title + '</td>' +
                '<td>' + formatDate(app.application_date) + '</td>' +
                '<td>' + app.status + '</td>' +
                '<td>' +
                    '<button class="btn btn-sm btn-outline-primary me-1" onclick="openEditApplicationModal(' +
                        app.id + ', ' + app.applicant_id + ', ' + app.job_id + ', \'' + app.application_date + '\', \'' + app.status + '\')">Edit</button>' +
                    '<button class="btn btn-sm btn-outline-danger" onclick="deleteApplication(' + app.id + ')">Delete</button>' +
                '</td>';
            tbody.appendChild(tr);
        });
    })
    .catch(function () {
        showToast('Error loading applications.', 'error');
    });
}

function filterApplications() {
    var input = document.getElementById('application-search');
    if (!input) return;
    var query = input.value.toLowerCase();
    var rows = document.querySelectorAll('#applications-table tbody tr');
    rows.forEach(function (row) {
        if (row.classList.contains('empty-row')) return;
        var text = row.textContent.toLowerCase();
        row.style.display = text.indexOf(query) > -1 ? '' : 'none';
    });
}

function checkEmptyStates() {
    var tbody = document.querySelector('#applications-table tbody');
    if (!tbody) return;
    if (tbody.querySelectorAll('tr').length === 0) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="5" style="text-align:center;">No applications found.</td></tr>';
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
