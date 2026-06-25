document.addEventListener("DOMContentLoaded", () => {
    // Check local time to resolve server-to-client timezone mismatch
    const checkEndedEvents = () => {
        const cards = document.querySelectorAll(".event-interactive-card");
        const now = new Date();

        for (let i = 0; i < cards.length; i++) {
            const card = cards[i];
            const endDateStr = card.dataset.endDate;
            if (!endDateStr) {
                continue;
            }

            const endDate = new Date(endDateStr);

            if (now > endDate) {
                card.classList.add("ended");

                const badgeContainer = card.querySelector(".badge-container");
                if (badgeContainer && !badgeContainer.querySelector(".ended-status-badge")) {
                    const endedBadge = document.createElement("span");
                    endedBadge.className = "ended-status-badge";
                    endedBadge.textContent = "Ended";
                    badgeContainer.appendChild(endedBadge);
                }

                const interestBtn = card.querySelector(".btn-interest");
                const notifyBtn = card.querySelector(".btn-notify");

                if (interestBtn) {
                    interestBtn.disabled = true;
                }
                if (notifyBtn) {
                    notifyBtn.disabled = true;
                }
            }
        }
    };

    const filterTodayEvents = () => {
        const today = new Date();
        const todayYear = today.getFullYear();
        const todayMonth = today.getMonth();
        const todayDate = today.getDate();

        let visibleCount = 0;
        document.querySelectorAll(".today-event-card").forEach(card => {
            const startDateStr = card.dataset.startDate;
            if (!startDateStr) return;
            const startDate = new Date(startDateStr);
            if (
                startDate.getFullYear() === todayYear &&
                startDate.getMonth() === todayMonth &&
                startDate.getDate() === todayDate
            ) {
                card.style.display = ""; // Show
                visibleCount++;
            } else {
                card.style.display = "none"; // Hide
            }
        });

        if (visibleCount === 0) {
            const grid = document.querySelector(".base-card-grid");
            if (grid) {
                grid.innerHTML = `
                    <div class="base-card welcome-card" style="grid-column: 1 / -1; text-align: center; padding: 2.5rem 1.5rem;">
                        <h2 class="welcome-title" style="margin-bottom: 0.5rem; font-size: 1.5rem; font-weight: 600; color: var(--text-color);">No Events Scheduled Today</h2>
                        <p class="welcome-text" style="color: var(--muted-color); font-size: 0.95rem;">Explore the map to see all upcoming events and schedule new ones!</p>
                        <div class="welcome-card-actions" style="margin-top: 1.5rem; display: flex; justify-content: center; gap: 0.75rem;">
                            <a href="${window.location.origin}/dashboard" class="base-button btn-small">Go to Dashboard</a>
                        </div>
                    </div>
                `;
            }
        }
    };

    filterTodayEvents();
    checkEndedEvents();
});
