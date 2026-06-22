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

function togglePasswordVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';
    const icon = btn.querySelector('i');
    if (icon) {
        icon.className = isPassword ? 'bi bi-eye-slash-fill' : 'bi bi-eye-fill';
    }
}

function copyToClipboard(text, friendlyName) {
    navigator.clipboard.writeText(text).then(() => {
        showToast(`Copied ${friendlyName} path to clipboard!`, 'success');
    }).catch(err => {
        console.error('Failed to copy path: ', err);
        showToast('Failed to copy path to clipboard.', 'error');
    });
}
