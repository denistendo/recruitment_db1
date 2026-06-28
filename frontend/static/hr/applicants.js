function getApplicantModal() {
    var el = document.getElementById('applicant-modal');
    if (!el) return null;
    var modal = new bootstrap.Modal(el);
    return modal;
}

function openEditApplicantModal(applicantId, userId, dateOfBirth, gender, phoneNumber, address) {
    var modal = getApplicantModal();
    if (!modal) return;
    document.getElementById('applicant-id').value = applicantId;
    document.getElementById('id_user').value = userId;
    document.getElementById('id_date_of_birth').value = dateOfBirth;
    document.getElementById('id_gender').value = gender;
    document.getElementById('id_phone_number').value = phoneNumber;
    document.getElementById('id_address').value = address;
    document.getElementById('applicant-modal-title').textContent = 'Edit Applicant';
    modal.show();
}

function submitApplicantForm(event) {
    event.preventDefault();
    var id = document.getElementById('applicant-id').value;
    var data = {
        user: document.getElementById('id_user').value,
        date_of_birth: document.getElementById('id_date_of_birth').value,
        gender: document.getElementById('id_gender').value,
        phone_number: document.getElementById('id_phone_number').value,
        address: document.getElementById('id_address').value
    };
    var url = id ? '/api/applicants/update/' + id + '/' : '/api/applicants/create/';
    var method = id ? 'PUT' : 'POST';

    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify(data)
    })
    .then(function (response) { return response.json(); })
    .then(function (result) {
        if (result.success) {
            var modal = getApplicantModal();
            if (modal) modal.hide();
            showToast('Applicant saved successfully.', 'success');
            refreshApplicantsTable();
        } else {
            showToast(result.error || 'Error saving applicant.', 'error');
        }
    })
    .catch(function () {
        showToast('Error saving applicant.', 'error');
    });
}

function deleteApplicant(applicantId) {
    if (!confirm('Are you sure you want to delete this applicant?')) return;
    fetch('/api/applicants/delete/' + applicantId + '/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(function (response) { return response.json(); })
    .then(function (result) {
        if (result.success) {
            showToast('Applicant deleted.', 'success');
            refreshApplicantsTable();
        } else {
            showToast('Error deleting applicant.', 'error');
        }
    })
    .catch(function () {
        showToast('Error deleting applicant.', 'error');
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

function refreshApplicantsTable() {
    var tbody = document.querySelector('#applicants-table tbody');
    if (!tbody) return;
    fetch('/api/applicants/')
    .then(function (response) { return response.json(); })
    .then(function (data) {
        tbody.innerHTML = '';
        if (!data.applicants || data.applicants.length === 0) {
            checkEmptyStates();
            return;
        }
        data.applicants.forEach(function (app) {
            var tr = document.createElement('tr');
            tr.innerHTML =
                '<td class="applicant-name-cell">' + (app.full_name || app.user_name || '') + '</td>' +
                '<td>' + genderBadge(app.gender) + '</td>' +
                '<td>' + formatDate(app.date_of_birth) + '</td>' +
                '<td>' + (app.phone_number || '') + '</td>' +
                '<td>' +
                    '<button class="btn btn-sm btn-outline-primary me-1" onclick="openEditApplicantModal(' +
                        app.id + ', ' + app.user_id + ', \'' + (app.date_of_birth || '') + '\', \'' + (app.gender || '') + '\', \'' + (app.phone_number || '') + '\', \'' + (app.address || '').replace(/'/g, "\\'") + '\')">Edit</button>' +
                    '<button class="btn btn-sm btn-outline-danger" onclick="deleteApplicant(' + app.id + ')">Delete</button>' +
                '</td>';
            tbody.appendChild(tr);
        });
        updateApplicantCount();
    })
    .catch(function () {
        showToast('Error loading applicants.', 'error');
    });
}

function genderBadge(gender) {
    if (!gender) return '';
    var g = gender.toLowerCase();
    if (g === 'male') return '<span class="badge" style="background:#3b82f6;">Male</span>';
    if (g === 'female') return '<span class="badge" style="background:#ec4899;">Female</span>';
    return '<span class="badge" style="background:#8b5cf6;">' + gender + '</span>';
}

function updateApplicantCount() {
    var countEl = document.getElementById('applicant-count');
    if (!countEl) return;
    var rows = document.querySelectorAll('#applicants-table tbody tr');
    var count = 0;
    rows.forEach(function (row) {
        if (!row.classList.contains('empty-row')) count++;
    });
    countEl.textContent = count;
}

function filterApplicants() {
    var input = document.getElementById('applicant-search');
    if (!input) return;
    var query = input.value.toLowerCase();
    var rows = document.querySelectorAll('#applicants-table tbody tr');
    rows.forEach(function (row) {
        if (row.classList.contains('empty-row')) return;
        var text = row.textContent.toLowerCase();
        row.style.display = text.indexOf(query) > -1 ? '' : 'none';
    });
}

function checkEmptyStates() {
    var tbody = document.querySelector('#applicants-table tbody');
    if (!tbody) return;
    if (tbody.querySelectorAll('tr').length === 0) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="5" style="text-align:center;">No applicants found.</td></tr>';
    }
    updateApplicantCount();
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
