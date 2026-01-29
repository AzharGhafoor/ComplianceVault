/**
 * Toast Notification Utility
 * Handles displaying temporary alert messages (Toasts) and persistent flash messages.
 */

class ToastManager {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'toast-container';
        document.body.appendChild(this.container);

        // Check for flash messages from redirection
        this.checkFlashMessage();
    }

    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - 'success', 'error', 'warning', 'info'
     * @param {number} duration - Time in ms before auto-dismiss (default 4000)
     */
    show(message, type = 'info', duration = 4000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        // Icon selection
        let icon = '';
        switch (type) {
            case 'success': icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>'; break;
            case 'error': icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'; break;
            case 'warning': icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'; break;
            default: icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
        }

        toast.innerHTML = `
            <div class="toast-icon">${icon}</div>
            <div class="toast-message">${message}</div>
            <button class="toast-close">&times;</button>
        `;

        // Close button event
        toast.querySelector('.toast-close').addEventListener('click', () => {
            this.dismiss(toast);
        });

        // Add to container
        this.container.appendChild(toast);

        // Auto dismiss
        if (duration > 0) {
            setTimeout(() => {
                this.dismiss(toast);
            }, duration);
        }
    }

    dismiss(toast) {
        toast.style.animation = 'toast-out 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards';
        toast.addEventListener('animationend', () => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
        });
    }

    success(msg, duration) { this.show(msg, 'success', duration); }
    error(msg, duration) { this.show(msg, 'error', duration); }
    warning(msg, duration) { this.show(msg, 'warning', duration); }
    info(msg, duration) { this.show(msg, 'info', duration); }

    /**
     * Set a message to be shown on the next page load (Flash Message)
     */
    static setFlash(message, type = 'success') {
        localStorage.setItem('cv_flash', JSON.stringify({ message, type }));
    }

    checkFlashMessage() {
        const flash = localStorage.getItem('cv_flash');
        if (flash) {
            try {
                const { message, type } = JSON.parse(flash);
                this.show(message, type);
            } catch (e) {
                console.error("Error parsing flash message", e);
            }
            localStorage.removeItem('cv_flash');
        }
    }
}

export const Toast = new ToastManager();
