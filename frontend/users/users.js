function openCreateUserModal() {
    const form = document.getElementById('create-user-form');
    form.reset();
    delete form.dataset.editId;
    
    document.querySelector('#user-modal h3').textContent = 'Create New User Profile';
    document.querySelector('#user-modal .btn-success').textContent = 'Save User';
    
    document.getElementById('user-password').required = true;
    document.getElementById('user-password').placeholder = 'Enter password (max 8 chars)';
    
    openModal('user-modal');
}

function openEditUserModal(userId, fullName, email, userType) {
    const form = document.getElementById('create-user-form');
    form.reset();
    form.dataset.editId = userId;
    
    document.querySelector('#user-modal h3').textContent = 'Edit User Profile';
    document.querySelector('#user-modal .btn-success').textContent = 'Update User';
    
    document.getElementById('user-fullname').value = fullName;
    document.getElementById('user-email').value = email;
    document.getElementById('user-type').value = userType;
    
    document.getElementById('user-password').required = false;
    document.getElementById('user-password').placeholder = 'Leave blank to keep current password';
    
    openModal('user-modal');
}

async function submitUserForm(event) {
    event.preventDefault();
    const form = document.getElementById('create-user-form');
    const editId = form.dataset.editId;
    
    const fullname = document.getElementById('user-fullname').value;
    const email = document.getElementById('user-email').value;
    const password = document.getElementById('user-password').value;
    const userType = document.getElementById('user-type').value;
    
    const payload = {
        full_name: fullname,
        email: email,
        user_type: userType
    };
    if (password) {
        payload.password = password;
    }
    
    const url = editId ? `/api/users/update/${editId}/` : '/api/users/create/';
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
            closeModal('user-modal');
            form.reset();
            delete form.dataset.editId;
            refreshUsersTable();
        } else {
            showToast(result.message || 'Error occurred.', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
}

async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user profile?')) return;
    
    try {
        const response = await fetch(`/api/users/delete/${userId}/`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast(result.message, 'success');
            const row = document.getElementById(`user-row-${userId}`);
            if (row) {
                row.remove();
            }
            checkEmptyStates();
        } else {
            showToast(result.message || 'Failed to delete user.', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
}

async function refreshUsersTable() {
    try {
        const response = await fetch('/api/users/');
        const result = await response.json();
        
        if (response.ok && result.users) {
            const tbody = document.getElementById('users-table-body');
            tbody.innerHTML = '';
            
            if (result.users.length === 0) {
                tbody.innerHTML = `
                    <tr id="users-empty-row">
                        <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                            No user records found in the database.
                        </td>
                    </tr>`;
                return;
            }
            
            result.users.forEach(u => {
                const tr = document.createElement('tr');
                tr.id = `user-row-${u.user_id}`;
                const escapedName = u.full_name.replace(/'/g, "\\'");
                const escapedEmail = u.email.replace(/'/g, "\\'");
                const escapedRole = u.user_type.replace(/'/g, "\\'");
                
                tr.innerHTML = `
                    <td>${u.user_id}</td>
                    <td class="user-name-cell">${u.full_name}</td>
                    <td>${u.email}</td>
                    <td><span class="role-badge role-${u.user_type.toLowerCase()}">${u.user_type}</span></td>
                    <td style="text-align: center;">
                        <button class="btn-edit" onclick="openEditUserModal(${u.user_id}, '${escapedName}', '${escapedEmail}', '${escapedRole}')">Edit</button>
                        <button class="btn-danger" onclick="deleteUser(${u.user_id})">Delete</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error('Error reloading users list:', error);
    }
}

function filterUsers() {
    const query = document.getElementById('search-users').value.toLowerCase();
    const rows = document.querySelectorAll('#users-table-body tr');
    
    rows.forEach(row => {
        if (row.id === 'users-empty-row') return;
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
    });
}

function checkEmptyStates() {
    const userRows = document.querySelectorAll('#users-table-body tr');
    if (userRows.length === 0 || (userRows.length === 1 && userRows[0].id === 'users-empty-row')) {
        refreshUsersTable();
    }
}
