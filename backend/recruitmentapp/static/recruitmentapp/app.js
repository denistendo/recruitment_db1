// ==============================================================================
// Recruitment Dashboard JavaScript Controllers
// Purpose:
//   Handles browser-side interactivity (tabs, forms, modals) and communicates
//   with the Django backend using AJAX Fetch calls to provide a smooth, 
//   React-like experience with zero page reloads.
// ==============================================================================

// ==========================================
// 1. NAVIGATION & TAB SWITCHING
// ==========================================

function switchTab(tabName) {
    document.querySelectorAll('.tab-section').forEach(section => {
        section.classList.remove('active');
    });
    document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
    });

    if (tabName === 'users') {
        document.getElementById('section-users').classList.add('active');
        document.getElementById('nav-users').classList.add('active');
        document.getElementById('dashboard-title').textContent = 'Users Directory';
        document.getElementById('dashboard-subtitle').textContent = 'Manage company recruiters, managers, and candidate accounts.';
    } else if (tabName === 'jobs') {
        document.getElementById('section-jobs').classList.add('active');
        document.getElementById('nav-jobs').classList.add('active');
        document.getElementById('dashboard-title').textContent = 'Job Vacancies';
        document.getElementById('dashboard-subtitle').textContent = 'Track and post active corporate job listings linked to departments.';
    }
}

// ==========================================
// 2. MODAL WINDOW CONTROLS
// ==========================================

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('open');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('open');
    }
}

// Helpers for opening modals in Create vs Edit mode
function openCreateUserModal() {
    const form = document.getElementById('create-user-form');
    form.reset();
    delete form.dataset.editId; // Remove edit flag
    
    // Set appropriate text
    document.querySelector('#user-modal h3').textContent = 'Create New User Profile';
    document.querySelector('#user-modal .btn-success').textContent = 'Save User';
    
    // Password must be required on create
    document.getElementById('user-password').required = true;
    document.getElementById('user-password').placeholder = 'Enter password (max 8 chars)';
    
    openModal('user-modal');
}

function openEditUserModal(userId, fullName, email, userType) {
    const form = document.getElementById('create-user-form');
    form.reset();
    form.dataset.editId = userId; // Store edit ID
    
    // Set appropriate text
    document.querySelector('#user-modal h3').textContent = 'Edit User Profile';
    document.querySelector('#user-modal .btn-success').textContent = 'Update User';
    
    // Pre-fill inputs
    document.getElementById('user-fullname').value = fullName;
    document.getElementById('user-email').value = email;
    document.getElementById('user-type').value = userType;
    
    // Password optional on edit
    document.getElementById('user-password').required = false;
    document.getElementById('user-password').placeholder = 'Leave blank to keep current password';
    
    openModal('user-modal');
}

function openCreateJobModal() {
    const form = document.getElementById('create-job-form');
    form.reset();
    delete form.dataset.editId;
    
    document.querySelector('#job-modal h3').textContent = 'Post New Job Vacancy';
    document.querySelector('#job-modal .btn-success').textContent = 'Post Job';
    
    openModal('job-modal');
}

function openEditJobModal(jobId, title, description, departmentId, postedDate, closingDate) {
    const form = document.getElementById('create-job-form');
    form.reset();
    form.dataset.editId = jobId;
    
    document.querySelector('#job-modal h3').textContent = 'Edit Job Posting';
    document.querySelector('#job-modal .btn-success').textContent = 'Update Job';
    
    // Pre-fill values
    document.getElementById('job-title').value = title;
    document.getElementById('job-description').value = description;
    document.getElementById('job-department').value = departmentId;
    
    // Dates need to be parsed from ISO format (YYYY-MM-DD) if present
    document.getElementById('job-posted-date').value = postedDate && postedDate !== 'None' ? postedDate : '';
    document.getElementById('job-closing-date').value = closingDate && closingDate !== 'None' ? closingDate : '';
    
    openModal('job-modal');
}

// ==========================================
// 3. TOAST FEEDBACK NOTIFICATIONS
// ==========================================

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icon = type === 'success' ? '✓' : '✗';
    toast.innerHTML = `<span style="margin-right: 0.5rem; font-weight: bold;">${icon}</span> ${message}`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => { toast.remove(); }, 300);
    }, 4000);
}

// ==========================================
// 4. USERS CRUD OPERATIONS
// ==========================================

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
    // Include password only if it is provided
    if (password) {
        payload.password = password;
    }
    
    // Determine edit vs create URL & Method
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

// ==========================================
// 5. JOBS CRUD OPERATIONS
// ==========================================

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
            closeModal('job-modal');
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
                        <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                            No job postings found in the database.
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
                    <td>${job.job_id}</td>
                    <td class="job-title-cell">${job.title}</td>
                    <td>${job.department_name}</td>
                    <td>${job.posted_date || '-'}</td>
                    <td>${job.closing_date || '-'}</td>
                    <td style="text-align: center;">
                        <button class="btn-edit" onclick="openEditJobModal(${job.job_id}, '${escapedTitle}', '${escapedDesc}', '${deptId}', '${job.posted_date}', '${job.closing_date}')">Edit</button>
                        <button class="btn-danger" onclick="deleteJob(${job.job_id})">Delete</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error('Error reloading jobs list:', error);
    }
}

// ==========================================
// 6. HELPER CHECKS & CLIENT-SIDE FILTERING
// ==========================================

function filterUsers() {
    const query = document.getElementById('search-users').value.toLowerCase();
    const rows = document.querySelectorAll('#users-table-body tr');
    
    rows.forEach(row => {
        if (row.id === 'users-empty-row') return;
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
    });
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
    const userRows = document.querySelectorAll('#users-table-body tr');
    if (userRows.length === 0 || (userRows.length === 1 && userRows[0].id === 'users-empty-row')) {
        refreshUsersTable();
    }
    
    const jobRows = document.querySelectorAll('#jobs-table-body tr');
    if (jobRows.length === 0 || (jobRows.length === 1 && jobRows[0].id === 'jobs-empty-row')) {
        refreshJobsTable();
    }
}
