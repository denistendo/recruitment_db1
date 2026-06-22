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

function copyToClipboard(text, friendlyName) {
    navigator.clipboard.writeText(text).then(() => {
        showToast(`Copied ${friendlyName} path to clipboard!`, 'success');
    }).catch(err => {
        console.error('Failed to copy path: ', err);
        showToast('Failed to copy path to clipboard.', 'error');
    });
}
