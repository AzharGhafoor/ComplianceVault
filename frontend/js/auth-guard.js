/**
 * Auth Guard
 * Prevents "Flash of Unauthenticated Content" (FOUC) by blocking rendering
 * until authentication is verified.
 * 
 * Usage: Include this script in the <head> of protected pages.
 * <script src="../js/auth-guard.js"></script>
 */

(function () {
    // 1. Immediately hide the body to prevent FOUC
    const style = document.createElement('style');
    style.id = 'auth-guard-style';
    style.innerHTML = 'body { display: none !important; }';
    document.head.appendChild(style);

    // 2. Check for token
    const token = localStorage.getItem('cv_token');

    if (!token) {
        // Not authenticated - redirect immediately
        // Use replace() so the back button doesn't return to this protected page
        const currentPath = window.location.pathname;
        const loginPath = currentPath.includes('/dashboard/') ? '../auth/login.html' : 'frontend/auth/login.html';

        // Store flash message for login page
        localStorage.setItem('cv_flash', JSON.stringify({
            message: 'Please sign in to access this page',
            type: 'error'
        }));

        window.location.replace(loginPath);
    } else {
        // Authenticated - Allow rendering
        // We use requestAnimationFrame to ensure the style removal happens 
        // after the browser has processed the "display: none"
        requestAnimationFrame(() => {
            const styleEl = document.getElementById('auth-guard-style');
            if (styleEl) {
                styleEl.remove();
            }
            // Add a fade-in effect for smoothness
            document.body.style.opacity = '0';
            document.body.style.transition = 'opacity 0.2s ease-in';
            requestAnimationFrame(() => {
                document.body.style.opacity = '1';
            });
        });
    }
})();
