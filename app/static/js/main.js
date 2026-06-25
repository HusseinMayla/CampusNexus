// ── Theme & Sidebar setup ─────────────────────────────────────────────────────

const toggle = document.getElementById('themeToggle');      // dark/light mode button
const hamburger = document.getElementById('hamburger');     // mobile menu button
const sidebar = document.querySelector('.base-sidebar');    // the left nav sidebar
const saved = localStorage.getItem('theme') || 'dark';     // load saved theme, default to dark
document.documentElement.setAttribute('data-theme', saved); // apply theme immediately on load

// Updates the 'active' class on nav links based on the current URL path and ?view= param.
// Called on load and whenever the URL changes (e.g. when toggling the events sidebar)
window.updateNavActiveStates = function () {
    const navItems = document.querySelectorAll('.base-nav-item');
    for (let i = 0; i < navItems.length; i++) {
        const link = navItems[i];
        if (link.href) {
            const linkUrl = new URL(link.href);
            const currentUrl = new URL(window.location.href);
            if (linkUrl.pathname === currentUrl.pathname) {
                const linkView = linkUrl.searchParams.get('view');
                const currentView = currentUrl.searchParams.get('view');
                if (linkView === currentView) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            } else {
                link.classList.remove('active');
            }
        }
    }
};
window.updateNavActiveStates();

// Toggle between dark and light theme, save preference to localStorage
toggle.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    let next = '';
    if (current === 'dark') {
        next = 'light';
    } else {
        next = 'dark';
    }
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
});

// Open/close the mobile sidebar on hamburger click
hamburger.addEventListener('click', () => {
    sidebar.classList.toggle('open');
});

// Close sidebar when clicking anywhere outside it
document.addEventListener('click', e => {
    if (!sidebar.contains(e.target) && !hamburger.contains(e.target)) {
        sidebar.classList.remove('open');
    }
});

// ── Notification badge polling ────────────────────────────────────────────────

// Polls the unread notification count every 15 seconds and updates the badge on the bell icon.
// Only runs when the user is authenticated (data-authenticated set on body by the template)
if (document.body.dataset.authenticated === 'true') {
    setInterval(async () => {
        try {
            const res = await fetch('/api/notifications/unread-count');
            if (!res.ok) {
                return;
            }
            const data = await res.json();
            const notifBtn = document.querySelector('.base-notification-btn');
            if (!notifBtn) {
                return;
            }
            let badge = notifBtn.querySelector('.notification-badge');
            if (data.count > 0) {
                // Create badge element if it doesn't exist yet
                if (!badge) {
                    badge = document.createElement('span');
                    badge.className = 'notification-badge';
                    notifBtn.appendChild(badge);
                }
                badge.textContent = data.count;
            } else if (badge) {
                // Remove badge when count drops to 0
                badge.remove();
            }
        } catch (err) {
            console.error('Failed to poll notifications', err);
        }
    }, 15000);
}

// ── Timezone formatter ────────────────────────────────────────────────────────

// Converts UTC timestamps stored in data-utc attributes into the user's local timezone.
// Templates render times in UTC; this runs on DOMContentLoaded to swap them to local time.
// Supports multiple formats via data-format attribute:
//   "time-only"       → "3:05 PM"
//   "full-date-time"  → "2026-06-25 15:05"
//   "date-time"       → "Jun 25, 3:05 PM"
//   "event-duration"  → "Jun 25, 3:05 PM - 4:00 PM" (uses data-end-utc for end time)
window.formatLocalTimes = function() {
    document.querySelectorAll(".local-time").forEach(el => {
        const utcStr = el.getAttribute("data-utc");
        if (!utcStr) return;
        const date = new Date(utcStr);
        if (isNaN(date.getTime())) return;

        const format = el.getAttribute("data-format");
        let formatted = "";

        const timeOptions = { hour: 'numeric', minute: '2-digit', hour12: true };
        const dateOptions = { month: 'short', day: 'numeric' };

        if (format === "time-only") {
            formatted = date.toLocaleTimeString([], timeOptions);
        } else if (format === "full-date-time") {
            const yyyy = date.getFullYear();
            const mm = String(date.getMonth() + 1).padStart(2, '0');
            const dd = String(date.getDate()).padStart(2, '0');
            const hh = String(date.getHours()).padStart(2, '0');
            const min = String(date.getMinutes()).padStart(2, '0');
            formatted = `${yyyy}-${mm}-${dd} ${hh}:${min}`;
        } else if (format === "date-time") {
            const datePart = date.toLocaleDateString([], dateOptions);
            const timePart = date.toLocaleTimeString([], timeOptions);
            formatted = `${datePart}, ${timePart}`;
        } else if (format === "event-duration") {
            const endUtcStr = el.getAttribute("data-end-utc");
            if (endUtcStr) {
                const endDate = new Date(endUtcStr);
                if (!isNaN(endDate.getTime())) {
                    const startOptions = { month: 'short', day: 'numeric' };
                    const startDateStr = date.toLocaleDateString([], startOptions);
                    const startTimeStr = date.toLocaleTimeString([], timeOptions);
                    const endTimeStr = endDate.toLocaleTimeString([], timeOptions);

                    // If same day: "Jun 25, 3:05 PM - 4:00 PM"
                    // If different days: "Jun 25, 3:05 PM - Jun 26, 4:00 PM"
                    if (date.toDateString() === endDate.toDateString()) {
                        formatted = `${startDateStr}, ${startTimeStr} - ${endTimeStr}`;
                    } else {
                        const endDateStr = endDate.toLocaleDateString([], startOptions);
                        formatted = `${startDateStr}, ${startTimeStr} - ${endDateStr}, ${endTimeStr}`;
                    }
                } else {
                    formatted = el.textContent;
                }
            } else {
                formatted = el.textContent;
            }
        } else {
            formatted = date.toLocaleString();
        }

        el.textContent = formatted;
        el.classList.remove("local-time"); // Avoid reprocessing if called again
    });
};

// Run timezone formatting after the DOM is fully loaded
document.addEventListener("DOMContentLoaded", () => {
    window.formatLocalTimes();
});

// Unified client-side campus search and filtering helper
window.filterCampuses = function() {
    const input = document.getElementById('campusSearch');
    if (!input) return;
    const filter = input.value.toLowerCase();
    const grid = document.getElementById('campusGrid');
    if (!grid) return;
    const items = grid.getElementsByClassName('campus-item');
    const noResults = document.getElementById('noResults');
    let visibleCount = 0;

    for (let i = 0; i < items.length; i++) {
        const nameEl = items[i].querySelector('.campus-name');
        const descEl = items[i].querySelector('.base-card-desc');
        const name = nameEl ? nameEl.textContent.toLowerCase() : '';
        const desc = descEl ? descEl.textContent.toLowerCase() : '';
        
        if (name.includes(filter) || desc.includes(filter)) {
            items[i].style.display = "";
            visibleCount++;
        } else {
            items[i].style.display = "none";
        }
    }

    if (noResults) {
        noResults.style.display = visibleCount === 0 ? "block" : "none";
    }
    grid.style.display = visibleCount === 0 ? "none" : "grid";
};

