const toggle    = document.getElementById('themeToggle');
const hamburger = document.getElementById('hamburger');
const sidebar   = document.querySelector('.base-sidebar');
const saved     = localStorage.getItem('theme') || 'dark';
document.documentElement.setAttribute('data-theme', saved);

window.updateNavActiveStates = function () {
    document.querySelectorAll('.base-nav-item').forEach(link => {
        if (link.href) {
            const linkUrl    = new URL(link.href);
            const currentUrl = new URL(window.location.href);
            if (linkUrl.pathname === currentUrl.pathname) {
                const linkView    = linkUrl.searchParams.get('view');
                const currentView = currentUrl.searchParams.get('view');
                link.classList.toggle('active', linkView === currentView);
            } else {
                link.classList.remove('active');
            }
        }
    });
};
window.updateNavActiveStates();

toggle.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    const next    = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
});

hamburger.addEventListener('click', () => {
    sidebar.classList.toggle('open');
});

document.addEventListener('click', e => {
    if (!sidebar.contains(e.target) && !hamburger.contains(e.target)) {
        sidebar.classList.remove('open');
    }
});

// Notification badge polling (only when authenticated)
if (document.body.dataset.authenticated === 'true') {
    setInterval(async () => {
        try {
            const res = await fetch('/api/notifications/unread-count');
            if (!res.ok) return;
            const data    = await res.json();
            const notifBtn = document.querySelector('.base-notification-btn');
            if (!notifBtn) return;
            let badge = notifBtn.querySelector('.notification-badge');
            if (data.count > 0) {
                if (!badge) {
                    badge = document.createElement('span');
                    badge.className = 'notification-badge';
                    notifBtn.appendChild(badge);
                }
                badge.textContent = data.count;
            } else if (badge) {
                badge.remove();
            }
        } catch (err) {
            console.error('Failed to poll notifications', err);
        }
    }, 15000);
}
