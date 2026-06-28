function getUserModal() {
    var el = document.getElementById('user-modal');
    if (!el) return null;
    var modal = new bootstrap.Modal(el);
    return modal;
}

function openCreateUserModal() {
    var modal = getUserModal();
    if (!modal) return;
    document.getElementById('user-form').reset();
    document.getElementById('user-id').value = '';
    document.getElementById('user-modal-title').textContent = 'Create User';
    modal.show();
}

function openEditUserModal(userId, fullName, email, userType) {
    var modal = getUserModal();
    if (!modal) return;
    document.getElementById('user-id').value = userId;
    document.getElementById('id_full_name').value = fullName;
    document.getElementById('id_email').value = email;
    document.getElementById('id_user_type').value = userType;
    document.getElementById('user-modal-title').textContent = 'Edit User';
    modal.show();
}

function submitUserForm(event) {
    event.preventDefault();
    var id = document.getElementById('user-id').value;
    var data = {
        full_name: document.getElementById('id_full_name').value,
        email: document.getElementById('id_email').value,
        user_type: document.getElementById('id_user_type').value
    };
    var url = id ? '/api/users/update/' + id + '/' : '/api/users/create/';
    var method = id ? 'PUT' : 'POST';

    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify(data)
    })
    .then(function (response) { return response.json(); })
    .then(function (result) {
        if (result.success) {
            var modal = getUserModal();
            if (modal) modal.hide();
            showToast('User saved successfully.', 'success');
            refreshUsersTable();
        } else {
            showToast(result.error || 'Error saving user.', 'error');
        }
    })
    .catch(function () {
        showToast('Error saving user.', 'error');
    });
}

function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user?')) return;
    fetch('/api/users/delete/' + userId + '/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(function (response) { return response.json(); })
    .then(function (result) {
        if (result.success) {
            showToast('User deleted.', 'success');
            refreshUsersTable();
        } else {
            showToast('Error deleting user.', 'error');
        }
    })
    .catch(function () {
        showToast('Error deleting user.', 'error');
    });
}

function refreshUsersTable() {
    var tbody = document.querySelector('#users-table tbody');
    if (!tbody) return;
    fetch('/api/users/')
    .then(function (response) { return response.json(); })
    .then(function (data) {
        tbody.innerHTML = '';
        if (!data.users || data.users.length === 0) {
            checkEmptyStates();
            return;
        }
        data.users.forEach(function (user) {
            var tr = document.createElement('tr');
            tr.innerHTML =
                '<td class="user-name-cell">' + user.full_name + '</td>' +
                '<td>' + user.email + '</td>' +
                '<td><span class="role-badge role-' + user.user_type.toLowerCase() + '">' + user.user_type + '</span></td>' +
                '<td>' +
                    '<button class="btn btn-sm btn-outline-primary me-1" onclick="openEditUserModal(' +
                        user.id + ', \'' + user.full_name.replace(/'/g, "\\'") + '\', \'' + user.email.replace(/'/g, "\\'") + '\', \'' + user.user_type.replace(/'/g, "\\'") + '\')">Edit</button>' +
                    '<button class="btn btn-sm btn-outline-danger" onclick="deleteUser(' + user.id + ')">Delete</button>' +
                '</td>';
            tbody.appendChild(tr);
        });
    })
    .catch(function () {
        showToast('Error loading users.', 'error');
    });
}

function filterUsers() {
    var input = document.getElementById('user-search');
    if (!input) return;
    var query = input.value.toLowerCase();
    var rows = document.querySelectorAll('#users-table tbody tr');
    rows.forEach(function (row) {
        if (row.classList.contains('empty-row')) return;
        var text = row.textContent.toLowerCase();
        row.style.display = text.indexOf(query) > -1 ? '' : 'none';
    });
}

function checkEmptyStates() {
    var tbody = document.querySelector('#users-table tbody');
    if (!tbody) return;
    if (tbody.querySelectorAll('tr').length === 0) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="4" style="text-align:center;">No users found.</td></tr>';
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
