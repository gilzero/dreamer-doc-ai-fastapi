// app/static/js/main.js

// Utility functions
const utils = {
    showLoading() {
        document.getElementById('loadingSpinner').classList.remove('d-none');
    },

    hideLoading() {
        document.getElementById('loadingSpinner').classList.add('d-none');
    },

    showToast(message, type = 'success') {
        const toastContainer = document.querySelector('.toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} fade-in`;
        toast.innerHTML = `
            <div class="toast-header">
                <i class="fas fa-${type === 'success' ? 'check-circle text-success' : 'exclamation-circle text-danger'} me-2"></i>
                <strong class="me-auto">${type === 'success' ? 'Success' : 'Error'}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">${message}</div>
        `;
        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        toast.addEventListener('hidden.bs.toast', () => toast.remove());
    },

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    formatDate(date) {
        return new Date(date).toLocaleString();
    },

    async fetchWithError(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'X-CSRF-Token': window.config.csrfToken,
                    ...(options.headers || {})
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'An error occurred');
            }

            return await response.json();
        } catch (error) {
            utils.showToast(error.message, 'error');
            throw error;
        }
    }
};

// Initialize theme
document.addEventListener('DOMContentLoaded', () => {
    // Set initial theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);

    // Theme toggle functionality
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = themeToggle.querySelector('i');

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';

        document.documentElement.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);

        themeIcon.className = `fas fa-${newTheme === 'light' ? 'moon' : 'sun'}`;
    });
});

// Export utils for other modules
window.utils = utils;