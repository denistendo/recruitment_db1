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
    /**
     * Purpose: Toggles visible panels between Users and Job Postings.
     * Relevance: Ensures tab components are hidden/shown instantly.
     */
    // 1. Remove active state from all sections and nav buttons
    document.querySelectorAll('.tab-section').forEach(section => {
        section.classList.remove('active');
    });
    document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
    });

    // 2. Activate target section and sidebar item
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
    /**
     * Purpose: Reveals the modal window card overlay.
     */
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('open');
    }
}

function closeModal(modalId) {
    /**
     * Purpose: Hides the modal window overlay.
     */
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('open');
    }
}

// ==========================================
// 3. TOAST FEEDBACK NOTIFICATIONS
// ==========================================

function showToast(message, type = 'success') {
    /**
     * Purpose: Renders a popup notification card that fades away after 4 seconds.
     * Relevance: Provides clean success or error confirmation to the operator.
     */
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Icon based on type
    const icon = type === 'success' ? '✓' : '✗';
    
    toast.innerHTML = `<span style="margin-right: 0.5rem; font-weight: bold;">${icon}</span> ${message}`;
    container.appendChild(toast);
    
    // Auto remove after 4 seconds
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
    /**
     * Purpose: Intercepts form submission, validates and sends user data to Django.
     */
    event.preventDefault(); // Stop standard form reload
    
    const fullname = document.getElementById('user-fullname').value;
    const email = document.getElementById('user-email').value;
    const password = document.getElementById('user-password').value;
    const userType = document.getElementById('user-type').value;
    
    const payload = {
        full_name: fullname,
        email: email,
        password: password,
        user_type: userType
    };
    
    try {
        const response = await fetch('/api/users/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast(result.message, 'success');
            closeModal('user-modal');
            document.getElementById('create-user-form').reset();
            refreshUsersTable(); // Update list dynamically
        } else {
            showToast(result.message || 'Failed to create user.', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
}

async function deleteUser(userId) {
    /**
     * Purpose: Deletes a user by ID using AJAX DELETE.
     * Relevance: Removes the row instantly from DOM if request is successful.
     */
    if (!confirm('Are you sure you want to delete this user profile?')) return;
    
    try {
        const response = await fetch(`/api/users/delete/${userId}/`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast(result.message, 'success');
            // Select the row in DOM and remove it immediately with a transition
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
    /**
     * Purpose: Refetches users from Django backend and updates the table view.
     */
    try {
        const response = await fetch('/api/users/');
        const result = await response.json();
        
        if (response.ok && result.users) {
            const tbody = document.getElementById('users-table-body');
            tbody.innerHTML = ''; // Clear previous items
            
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
                tr.innerHTML = `
                    <td>${u.user_id}</td>
                    <td class="user-name-cell">${u.full_name}</td>
                    <td>${u.email}</td>
                    <td><span class="role-badge role-${u.user_type.toLowerCase()}">${u.user_type}</span></td>
                    <td style="text-align: center;">
                        <button class="btn btn-danger" onclick="deleteUser(${u.user_id})">Delete</button>
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
    /**
     * Purpose: Handles the job creation background submission.
     */
    event.preventDefault();
    
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
    
    try {
        const response = await fetch('/api/jobs/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast(result.message, 'success');
            closeModal('job-modal');
            document.getElementById('create-job-form').reset();
            refreshJobsTable();
        } else {
            showToast(result.message || 'Failed to post job.', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    }
}

async function deleteJob(jobId) {
    /**
     * Purpose: Deletes a job by ID.
     */
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
    /**
     * Purpose: Refetches jobs and repopulates the grid.
     */
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
                tr.innerHTML = `
                    <td>${job.job_id}</td>
                    <td class="job-title-cell">${job.title}</td>
                    <td>${job.department_name}</td>
                    <td>${job.posted_date || '-'}</td>
                    <td>${job.closing_date || '-'}</td>
                    <td style="text-align: center;">
                        <button class="btn btn-danger" onclick="deleteJob(${job.job_id})">Delete</button>
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
    /**
     * Purpose: Instant client-side text filtering as you type.
     */
    const query = document.getElementById('search-users').value.toLowerCase();
    const rows = document.querySelectorAll('#users-table-body tr');
    
    rows.forEach(row => {
        if (row.id === 'users-empty-row') return;
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
    });
}

function filterJobs() {
    /**
     * Purpose: Instant client-side job filtering.
     */
    const query = document.getElementById('search-jobs').value.toLowerCase();
    const rows = document.querySelectorAll('#jobs-table-body tr');
    
    rows.forEach(row => {
        if (row.id === 'jobs-empty-row') return;
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
    });
}

function checkEmptyStates() {
    /**
     * Purpose: Ensures that if all items are deleted, the placeholder empty state shows up.
     */
    const userRows = document.querySelectorAll('#users-table-body tr');
    if (userRows.length === 0 || (userRows.length === 1 && userRows[0].id === 'users-empty-row')) {
        refreshUsersTable(); // Re-render placeholder row
    }
    
    const jobRows = document.querySelectorAll('#jobs-table-body tr');
    if (jobRows.length === 0 || (jobRows.length === 1 && jobRows[0].id === 'jobs-empty-row')) {
        refreshJobsTable();
    }
}
