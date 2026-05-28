/* ═══════════════════════════════════════════════════════════════
   Agora — campus_map.js
   ════════════════════════════════════════════════════════════════ */

let _mapConfirmAction = null;
function showMapConfirm(msg, action) {
  const overlay = document.getElementById('mapConfirmOverlay');
  document.getElementById('mapConfirmMsg').textContent = msg;
  _mapConfirmAction = action;
  overlay.style.display = 'flex';
}
function closeMapConfirm() {
  document.getElementById('mapConfirmOverlay').style.display = 'none';
  _mapConfirmAction = null;
}
function doMapConfirm() {
  const action = _mapConfirmAction;
  closeMapConfirm();
  if (action) action();
}

document.addEventListener("DOMContentLoaded", () => {
  // ── DOM State ────────────────────────────────────────────────
  const configEl = document.getElementById("workspaceConfig");
  if (!configEl) return;

  const CAMPUS_ID = parseInt(configEl.dataset.campusId, 10);
  const IS_ADMIN = configEl.dataset.isAdmin === "true";

  let pins = [];
  let placementMode = "none"; // 'none', 'event', 'pin'
  let activeFilter = "all";
  let activePopover = null;
  let tempMarker = null;

  // ── Selectors ────────────────────────────────────────────────
  const blueprintCard = document.getElementById("blueprintCard");
  const blueprintCanvasWrapper = document.getElementById("blueprintCanvasWrapper");
  const blueprintImage = document.getElementById("blueprintImage");
  const pinsContainer = document.getElementById("pinsContainer");
  const blueprintBlurOverlay = document.getElementById("blueprintBlurOverlay");
  const placementGoldCaption = document.getElementById("placementGoldCaption");
  
  const eventsSidebar = document.getElementById("eventsSidebar");
  const eventsListContainer = document.getElementById("eventsListContainer");
  
  // Buttons
  const btnToggleEvents = document.getElementById("btnToggleEvents");
  const btnCloseSidebar = document.getElementById("btnCloseSidebar");
  const btnAddEvent = document.getElementById("btnAddEvent");
  const btnSidebarAddEvent = document.getElementById("btnSidebarAddEvent");
  const btnAddPin = document.getElementById("btnAddPin");
  
  // Modals & Forms
  const eventModalOverlay = document.getElementById("eventModalOverlay");
  const eventCreationForm = document.getElementById("eventCreationForm");
  const btnCloseEventModal = document.getElementById("btnCloseEventModal");
  const btnCancelEventModal = document.getElementById("btnCancelEventModal");
  const eventFormError = document.getElementById("eventFormError");
  
  const pinModalOverlay = document.getElementById("pinModalOverlay");
  const pinCreationForm = document.getElementById("pinCreationForm");
  const btnClosePinModal = document.getElementById("btnClosePinModal");
  const btnCancelPinModal = document.getElementById("btnCancelPinModal");
  const pinFormError = document.getElementById("pinFormError");

  const btnColumnAddClub = document.getElementById("btnColumnAddClub");
  const btnColumnAddOffice = document.getElementById("btnColumnAddOffice");
  const btnSelectLocationOnMap = document.getElementById("btnSelectLocationOnMap");
  const btnClearPinLocation = document.getElementById("btnClearPinLocation");
  const pinLocationStatusText = document.getElementById("pinLocationStatusText");
  const pinLatInput = document.getElementById("pinLat");
  const pinLngInput = document.getElementById("pinLng");

  function updateModalLocationStatus() {
    if (!pinLocationStatusText) return;
    const lat = pinLatInput ? pinLatInput.value : "";
    const lng = pinLngInput ? pinLngInput.value : "";
    const selectedRadio = document.querySelector('input[name="pinType"]:checked');
    const type = selectedRadio ? selectedRadio.value : "club";
    
    if (lat && lng) {
      pinLocationStatusText.textContent = `📍 Selected: ${parseFloat(lat).toFixed(1)}%, ${parseFloat(lng).toFixed(1)}%`;
      if (btnClearPinLocation) btnClearPinLocation.classList.remove("hidden");
    } else {
      if (type === "club") {
        pinLocationStatusText.textContent = "⚪ No location selected (Optional)";
      } else {
        pinLocationStatusText.textContent = "⚪ No location selected (Required)";
      }
      if (btnClearPinLocation) btnClearPinLocation.classList.add("hidden");
    }
  }

  // SVG Icons payload
  const SVG_ICONS = {
    club: `<svg viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>`,
    office: `<svg viewBox="0 0 24 24"><path d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10zm-2-8h-2v2h2v-2zm0 4h-2v2h2v-2z"/></svg>`,
    event: `<svg viewBox="0 0 24 24"><path d="M17 12h-5v5h5v-5zM16 1v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2h-1V1h-2zm3 18H5V8h14v11z"/></svg>`,
  };

  // ── Init & Fetch Data ────────────────────────────────────────
  async function init() {
    await fetchAllPins();
    
    // Check URL parameters for starting state
    const params = new URLSearchParams(window.location.search);
    if (params.get("view") === "events") {
      openSidebar();
    } else {
      // By default collapse the sidebar
      eventsSidebar.classList.add("collapsed");
    }
  }

  async function fetchAllPins() {
    try {
      const res = await fetch(`/api/map-data/${CAMPUS_ID}`);
      if (!res.ok) throw new Error("Failed to load map data");
      pins = await res.json();
      renderAllPins();
      renderEventsList();
    } catch (err) {
      console.error(err);
    }
  }

  // ── Rendering Pins ───────────────────────────────────────────
  function renderAllPins() {
    // Clear old pins except overlays/temp markers
    pinsContainer.innerHTML = "";
    
    pins.forEach((pin) => {
      if (pin.lat === null || pin.lng === null || pin.lat === undefined || pin.lng === undefined) {
        return;
      }
      const pinEl = document.createElement("div");
      pinEl.className = `blueprint-pin pin-${pin.type}`;
      
      // Filter check
      if (activeFilter !== "all" && pin.type !== activeFilter) {
        pinEl.classList.add("filtered-out");
      }
      pinEl.style.left = `${pin.lng}%`;
      pinEl.style.top = `${pin.lat}%`;
      pinEl.dataset.type = pin.type;
      pinEl.dataset.id = pin.id;
      
      // Dynamic Pin Sizing based on participation count (max size 56px, base 32px)
      if (pin.type === "event") {
        const baseSize = 32;
        const maxSize = 56;
        const count = pin.participation_count || 0;
        const pinSize = Math.min(maxSize, baseSize + count * 4);
        pinEl.style.width = `${pinSize}px`;
        pinEl.style.height = `${pinSize}px`;
      }
      
      pinEl.innerHTML = `
        <svg viewBox="0 0 32 32" class="geometric-pin-svg" style="width: 100%; height: 100%; position: absolute; top: 0; left: 0; pointer-events: none; z-index: 1;">
          <defs>
            <linearGradient id="grad-club-${pin.id}" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#c8a96e" />
              <stop offset="100%" stop-color="#8a7048" />
            </linearGradient>
            <linearGradient id="grad-office-${pin.id}" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#3b82f6" />
              <stop offset="100%" stop-color="#1d4ed8" />
            </linearGradient>
            <linearGradient id="grad-event-${pin.id}" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#f43f5e" />
              <stop offset="100%" stop-color="#be123c" />
            </linearGradient>
          </defs>
          <!-- 2 lines intersecting at bottom tip (16,32) and tangent to circle centered at (16,12) with radius 8 -->
          <path d="M 16 32 L 8.67 15.2 A 8 8 0 1 1 23.33 15.2 Z" 
                fill="url(#grad-${pin.type}-${pin.id})" 
                stroke="var(--color-pin-border)" 
                stroke-width="1.5" />
        </svg>
        <div class="blueprint-pin-icon">
          ${SVG_ICONS[pin.type] || ""}
        </div>
      `;
      
      // Active Event Glow Effects & Pulses or Ended Gray States
      if (pin.type === "event" && pin.date && pin.end_date) {
        const now = new Date();
        const isEventActive = new Date(pin.date) <= now && now <= new Date(pin.end_date);
        const isEventEnded = now > new Date(pin.end_date);
        if (isEventActive) {
          pinEl.classList.add("active-now");
          const halo = document.createElement("div");
          halo.className = "active-halo";
          pinEl.appendChild(halo);
        } else if (isEventEnded) {
          pinEl.classList.add("ended");
        }
      }
      
      // Below-pin text labels for premium readability
      const labelEl = document.createElement("div");
      labelEl.className = "pin-label";
      labelEl.textContent = pin.name;
      pinEl.appendChild(labelEl);
      
      // Setup click for Tooltip Popover
      pinEl.addEventListener("click", (e) => {
        e.stopPropagation();
        showPopover(pin, pinEl);
      });
      
      pinsContainer.appendChild(pinEl);
    });
  }

  // ── Rendering Events Sidebar List ───────────────────────────
  function renderEventsList() {
    eventsListContainer.innerHTML = "";
    
    const eventPins = pins.filter(p => p.type === "event");
    
    // Sort events: closest start time first
    eventPins.sort((a, b) => new Date(a.date) - new Date(b.date));
    
    if (eventPins.length === 0) {
      eventsListContainer.innerHTML = `<p class="empty-text">No upcoming campus events. Be the first to schedule one!</p>`;
      return;
    }
    
    eventPins.forEach((event) => {
      const card = document.createElement("div");
      card.className = "event-sidebar-card";
      card.dataset.id = event.id;
      
      const now = new Date();
      const isEventActive = new Date(event.date) <= now && now <= new Date(event.end_date);
      const isEventEnded = now > new Date(event.end_date);
      
      let activeBadge = "";
      if (isEventActive) {
        activeBadge = `<span class="active-now-badge"><span class="active-now-dot"></span>Active Now</span>`;
      } else if (isEventEnded) {
        activeBadge = `<span class="ended-badge">Ended</span>`;
        card.classList.add("ended");
      }

      const pCount = event.participation_count || 0;
      const popPill = pCount > 0 
        ? `<span class="card-popularity-badge has-interest">👥 ${pCount} interested</span>`
        : `<span class="card-popularity-badge">👥 0 interested</span>`;

      const isCreatorOrAdmin = event.is_creator || IS_ADMIN;
      const deleteBtn = isCreatorOrAdmin 
        ? `<button class="event-delete-btn" data-id="${event.id}">Delete</button>` 
        : "";

      // Action buttons toggle active states
      const interestedClass = event.is_interested ? "active" : "";
      const interestedIcon = event.is_interested ? "★" : "☆";
      const interestedText = event.is_interested ? "Interested" : "Interested";
      
      const notifyClass = event.want_notification ? "active" : "";
      const notifyIcon = event.want_notification ? "🔔" : "🔕";
      const notifyText = event.want_notification ? "Notify Active" : "Notify Me";

      const disabledAttr = isEventEnded ? "disabled style='opacity: 0.5; cursor: not-allowed;'" : "";

      card.innerHTML = `
        <div class="card-summary-row">
          <div class="card-title-section">
            <div class="card-title-badge-row">
              <h4>${escapeHtml(event.name)}</h4>
              ${activeBadge}
            </div>
            <div class="event-time">
              <span>📅 ${formatEventDuration(event.date, event.end_date)}</span>
            </div>
            <div style="margin-top: 2px;">
              ${popPill}
            </div>
          </div>
          <span class="accordion-chevron">▼</span>
        </div>
        
        <div class="card-expanded-content">
          <p class="event-details-text">${escapeHtml(event.description || "No description provided.")}</p>
          <div class="event-details-meta">
            <div class="event-meta-item">👤 <strong>Host:</strong> ${escapeHtml(event.creator_name || "Anonymous")}</div>
          </div>
          <div class="event-actions-bar">
            <button class="toggle-btn toggle-btn-interested ${interestedClass}" data-action="interested" ${disabledAttr}>
              <span>${interestedIcon}</span> ${interestedText}
            </button>
            <button class="toggle-btn toggle-btn-notify ${notifyClass}" data-action="notify" ${disabledAttr}>
              <span>${notifyIcon}</span> ${notifyText}
            </button>
          </div>
          <div style="display:flex; justify-content: flex-end; margin-top: 4px;">
            ${deleteBtn}
          </div>
        </div>
      `;
      
      // Micro-interactions: hover event card highlights map pin
      card.addEventListener("mouseenter", () => {
        highlightPin("event", event.id);
      });
      card.addEventListener("mouseleave", () => {
        unhighlightPin("event", event.id);
      });
      
      // Click summary row toggles accordion expand & flies popover on map
      const summaryRow = card.querySelector(".card-summary-row");
      summaryRow.addEventListener("click", () => {
        const wasExpanded = card.classList.contains("expanded");
        
        // Collapse all others
        document.querySelectorAll(".event-sidebar-card").forEach(c => c.classList.remove("expanded"));
        
        if (!wasExpanded) {
          card.classList.add("expanded");
          
          // Open map popover
          const pinEl = document.querySelector(`.blueprint-pin[data-type="event"][data-id="${event.id}"]`);
          if (pinEl) {
            showPopover(event, pinEl);
            pinEl.classList.add("pulsing-appeal");
            setTimeout(() => pinEl.classList.remove("pulsing-appeal"), 1500);
          }
        } else {
          closePopover();
        }
      });
      
      // Wire up toggle button actions
      const btnInterest = card.querySelector(".toggle-btn-interested");
      btnInterest.addEventListener("click", (e) => {
        e.stopPropagation();
        if (isEventEnded) return;
        toggleInterestNotify(event.id, "interested");
      });
      
      const btnNotify = card.querySelector(".toggle-btn-notify");
      btnNotify.addEventListener("click", (e) => {
        e.stopPropagation();
        if (isEventEnded) return;
        toggleInterestNotify(event.id, "notify");
      });
      
      // Delete event button click
      const delBtn = card.querySelector(".event-delete-btn");
      if (delBtn) {
        delBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          deletePin("event", event.id);
        });
      }
      
      eventsListContainer.appendChild(card);
    });
  }

  // ── Custom Popover / Tooltip Logic ────────────────────────────
  function showPopover(pin, pinEl) {
    closePopover();
    
    const popover = document.createElement("div");
    popover.className = "pin-popover";
    
    const isCreatorOrAdmin = pin.is_creator || IS_ADMIN;
    const deleteHtml = isCreatorOrAdmin 
      ? `<button class="popover-delete-btn">Delete location pin</button>`
      : "";
      
    let metaHtml = "";
    if (pin.type === "event" && pin.date) {
      metaHtml = `<div class="popover-meta">📅 ${formatEventDuration(pin.date, pin.end_date)}</div>`;
    }

    let popoverHeaderRow = `<h4 class="popover-title">${escapeHtml(pin.name)}</h4>`;
    let popoverActionsHtml = "";
    
    if (pin.type === "event") {
      const now = new Date();
      const isEventActive = new Date(pin.date) <= now && now <= new Date(pin.end_date);
      const isEventEnded = now > new Date(pin.end_date);
      
      let activeBadge = "";
      if (isEventActive) {
        activeBadge = `<span class="popover-active-badge">Active</span>`;
      } else if (isEventEnded) {
        activeBadge = `<span class="popover-active-badge" style="background: rgba(100,116,139,0.12); border-color: rgba(100,116,139,0.4); color: #cbd5e1;">Ended</span>`;
      }
      
      const pCount = pin.participation_count || 0;
      const popText = `👥 ${pCount} interested`;
      
      popoverHeaderRow = `
        <div class="popover-header-row">
          <h4 class="popover-title" style="margin:0;">${escapeHtml(pin.name)}</h4>
          ${activeBadge}
        </div>
        <div style="margin-top: 2px; margin-bottom: 6px;">
          <span class="popover-popularity-count">${popText}</span>
        </div>
      `;
      
      const interestedClass = pin.is_interested ? "active" : "";
      const interestedIcon = pin.is_interested ? "★" : "☆";
      
      const notifyClass = pin.want_notification ? "active" : "";
      const notifyIcon = pin.want_notification ? "🔔" : "🔕";
      
      const disabledAttr = isEventEnded ? "disabled style='opacity: 0.5; cursor: not-allowed;'" : "";
      
      popoverActionsHtml = `
        <div class="event-actions-bar" style="margin-top: 10px;">
          <button class="toggle-btn toggle-btn-interested ${interestedClass}" data-action="interested" style="padding: 4px 8px; font-size: 0.72rem;" title="Interested" ${disabledAttr}>
            <span>${interestedIcon}</span>
          </button>
          <button class="toggle-btn toggle-btn-notify ${notifyClass}" data-action="notify" style="padding: 4px 8px; font-size: 0.72rem;" title="Notify Me" ${disabledAttr}>
            <span>${notifyIcon}</span>
          </button>
        </div>
      `;
    }

    popover.innerHTML = `
      <div class="popover-type-bar popover-bar-${pin.type}"></div>
      ${popoverHeaderRow}
      ${metaHtml}
      <p class="popover-desc" style="margin:0; line-height: 1.4;">${escapeHtml(pin.description || "No description provided.")}</p>
      ${popoverActionsHtml}
      ${deleteHtml}
    `;
    
    // Position popover relative to the pin
    pinEl.appendChild(popover);
    
    // Elevate clicked pin's z-index so popover stays on top
    pinEl.style.zIndex = "600";
    
    // Triggers layout calculation so transition opacity works smoothly
    popover.getBoundingClientRect();
    popover.classList.add("visible");
    
    activePopover = { popover, pinEl, pin };
    
    // Wire up popover event action buttons
    if (pin.type === "event") {
      const now = new Date();
      const isEventEnded = now > new Date(pin.end_date);

      const popBtnInterest = popover.querySelector(".toggle-btn-interested");
      popBtnInterest.addEventListener("click", (e) => {
        e.stopPropagation();
        if (isEventEnded) return;
        toggleInterestNotify(pin.id, "interested");
      });
      
      const popBtnNotify = popover.querySelector(".toggle-btn-notify");
      popBtnNotify.addEventListener("click", (e) => {
        e.stopPropagation();
        if (isEventEnded) return;
        toggleInterestNotify(pin.id, "notify");
      });
    }
    
    // Delete action
    const popDelBtn = popover.querySelector(".popover-delete-btn");
    if (popDelBtn) {
      popDelBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        deletePin(pin.type, pin.id);
      });
    }
  }

  function closePopover() {
    if (activePopover) {
      const { popover, pinEl } = activePopover;
      popover.classList.remove("visible");
      // Reset z-index
      pinEl.style.zIndex = "";
      setTimeout(() => {
        if (popover && popover.parentNode === pinEl) {
          pinEl.removeChild(popover);
        }
      }, 200);
      activePopover = null;
    }
  }

  // Highlight marker mapping
  function highlightPin(type, id) {
    const pinEl = document.querySelector(`.blueprint-pin[data-type="${type}"][data-id="${id}"]`);
    if (pinEl) {
      if (pinEl.classList.contains("filtered-out")) {
        pinEl.classList.add("hover-reveal");
      }
      pinEl.style.transform = "translate(-50%, -50%) rotate(-45deg) scale(1.35)";
      pinEl.style.zIndex = "500";
    }
  }

  function unhighlightPin(type, id) {
    const pinEl = document.querySelector(`.blueprint-pin[data-type="${type}"][data-id="${id}"]`);
    if (pinEl) {
      pinEl.classList.remove("hover-reveal");
      pinEl.style.transform = "";
      pinEl.style.zIndex = "";
    }
  }

  // ── Delete Pin / Event ────────────────────────────────────────
  async function deletePin(type, id) {
    showMapConfirm(`Remove this ${type}?`, async () => {
      try {
        const res = await fetch(`/api/pin/delete/${type}/${id}`, { method: "DELETE" });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.error || "Failed to delete");
        }

        closePopover();
        pins = pins.filter(p => !(p.type === type && p.id === id));
        renderAllPins();
        renderEventsList();
        document.querySelector(`.legacy-list-card[data-pin-type="${type}"][data-pin-id="${id}"]`)?.remove();
      } catch (err) {
        alert(err.message);
      }
    });
  }

  // ── Toggle Interest & Notifications (AJAX POST) ───────────────
  async function toggleInterestNotify(eventId, action) {
    try {
      const res = await fetch(`/api/event/${eventId}/interest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: action })
      });

      if (!res.ok) throw new Error("Failed to toggle interest status");
      const data = await res.json();
      
      // Update local state in pins array
      const eventPin = pins.find(p => p.type === "event" && p.id === eventId);
      if (eventPin) {
        eventPin.is_interested = data.is_interested;
        eventPin.want_notification = data.want_notification;
        eventPin.participation_count = data.participation_count;
        
        // Re-render
        renderAllPins();
        renderEventsList();
        
        // Keep active popover open if matching
        if (activePopover && activePopover.pin.type === "event" && activePopover.pin.id === eventId) {
          const pinEl = document.querySelector(`.blueprint-pin[data-type="event"][data-id="${eventId}"]`);
          if (pinEl) {
            showPopover(eventPin, pinEl);
          }
        }
        
        // Keep sidebar card expanded
        const cardEl = document.querySelector(`.event-sidebar-card[data-id="${eventId}"]`);
        if (cardEl) {
          cardEl.classList.add("expanded");
        }
      }
    } catch (err) {
      console.error(err);
      alert(err.message);
    }
  }

  // ── Add card to legacy clubs/offices list ─────────────────────
  function prependLegacyCard(pin) {
    const keyword = pin.type === 'club' ? 'Club' : 'Office';
    let list = null;
    document.querySelectorAll('.legacy-column').forEach(col => {
      if (col.querySelector('h3')?.textContent.includes(keyword)) {
        list = col.querySelector('.legacy-card-list');
      }
    });
    if (!list) return;
    list.querySelector('.empty-text')?.remove();
    const card = document.createElement('div');
    card.className = 'legacy-list-card';
    card.dataset.pinType = pin.type;
    card.dataset.pinId = pin.id;
    card.innerHTML = `
      <div class="card-header">
        <h4>${escapeHtml(pin.name)}</h4>
        ${IS_ADMIN ? `
        <button class="card-delete-btn" onclick="showMapConfirm('Delete this ${pin.type}?', () => document.getElementById('delPin_${pin.type}_${pin.id}').submit())">🗑️</button>
        <form id="delPin_${pin.type}_${pin.id}" action="/campus/${CAMPUS_ID}/delete-${pin.type}/${pin.id}" method="POST" style="display:none;"></form>
        ` : ''}
      </div>
      <p>${escapeHtml(pin.description || 'No description provided.')}</p>
    `;
    list.prepend(card);
  }

  // ── Interactive Location Choosing ─────────────────────────────
  function enterPlacementMode(type) {
    closePopover();
    placementMode = type;
    
    // Enter visual selection mode: center card, show gold caption & full-viewport overlay
    blueprintCard.classList.add("active-placement");
    blueprintCanvasWrapper.classList.add("choosing-location");
    blueprintBlurOverlay.classList.remove("hidden");
    placementGoldCaption.classList.remove("hidden");
    
    // Hide all existing pins while creating a new one to declutter map
    const pinsEls = document.querySelectorAll(".blueprint-pin");
    pinsEls.forEach(p => p.style.display = "none");
    
    // Reset temp marker
    removeTempMarker();
  }

  function exitPlacementMode() {
    placementMode = "none";
    
    // Exit visual selection: restore card position, hide gold caption & full-viewport overlay
    blueprintCard.classList.remove("active-placement");
    blueprintCanvasWrapper.classList.remove("choosing-location");
    blueprintBlurOverlay.classList.add("hidden");
    placementGoldCaption.classList.add("hidden");
    
    // Restore all pins visibility
    renderAllPins();
    removeTempMarker();
  }

  function removeTempMarker() {
    if (tempMarker) {
      tempMarker.remove();
      tempMarker = null;
    }
  }

  // ── Date inputs setup & duration toggling ─────────────────────
  const eventDateInput = document.getElementById("eventDate");
  const eventDurationSelect = document.getElementById("eventDuration");
  const customDurationGroup = document.getElementById("customDurationGroup");
  const customDurationInput = document.getElementById("customDuration");

  // Toggle Custom Duration Group display
  if (eventDurationSelect && customDurationGroup) {
    eventDurationSelect.addEventListener("change", function () {
      customDurationGroup.classList.toggle("hidden", this.value !== "custom");
    });
  }

  // Helper to dynamically set min allowed local date-time (now)
  function enforceMinDateLimit() {
    if (!eventDateInput) return;
    const nowLocal = new Date(Date.now() - new Date().getTimezoneOffset() * 60000);
    eventDateInput.min = nowLocal.toISOString().slice(0, 16);
  }

  // Blueprint Map click location capture
  blueprintCanvasWrapper.addEventListener("click", (e) => {
    if (placementMode === "none") return;
    
    // Prevent event bubbling
    e.stopPropagation();
    
    // Capture accurate percentage positions based on image dimensions
    const rect = blueprintImage.getBoundingClientRect();
    const xPercent = ((e.clientX - rect.left) / rect.width) * 100;
    const yPercent = ((e.clientY - rect.top) / rect.height) * 100;
    
    // Place temp pulsing marker on map immediately (preview state)
    removeTempMarker();
    tempMarker = document.createElement("div");
    tempMarker.className = "temp-map-marker";
    tempMarker.style.left = `${xPercent}%`;
    tempMarker.style.top = `${yPercent}%`;
    pinsContainer.appendChild(tempMarker);
    
    // Display Modal popup with a slight visual expansion delay
    setTimeout(() => {
      if (placementMode === "event") {
        document.getElementById("eventLat").value = yPercent;
        document.getElementById("eventLng").value = xPercent;
        enforceMinDateLimit();
        openModal(eventModalOverlay);
      } else if (placementMode === "pin") {
        document.getElementById("pinLat").value = yPercent;
        document.getElementById("pinLng").value = xPercent;
        updateModalLocationStatus();
        openModal(pinModalOverlay);
      }
    }, 220);
  });

  // Clicking outside map blueprint cancels picker or cancels popup
  document.addEventListener("click", (e) => {
    if (placementMode !== "none") {
      // If clicked outside the blueprint wrapper and modal dialogs, cancel selection
      const isModalClick = eventModalOverlay.contains(e.target) || (pinModalOverlay && pinModalOverlay.contains(e.target));
      if (!blueprintCanvasWrapper.contains(e.target) && !isModalClick) {
        exitPlacementMode();
      }
    } else {
      // Close open popovers
      closePopover();
    }
  });

  // ── Dialog Modals overlays logic ──────────────────────────────
  function openModal(overlay) {
    overlay.classList.remove("hidden");
  }

  // Keep temporary marker visible during creation flow
  function closeModal(overlay) {
    overlay.classList.add("hidden");
    removeTempMarker();
  }

  // ── Forms Submissions (AJAX POST) ─────────────────────────────
  
  // Submit Create Event
  eventCreationForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    eventFormError.classList.add("hidden");
    eventFormError.textContent = "";
    
    const title = document.getElementById("eventTitle").value.trim();
    const desc = document.getElementById("eventDescription").value.trim();
    const dateVal = eventDateInput.value; // start date string
    const lat = parseFloat(document.getElementById("eventLat").value);
    const lng = parseFloat(document.getElementById("eventLng").value);
    
    if (!title || !dateVal || isNaN(lat) || isNaN(lng)) {
      eventFormError.textContent = "Please fill in all required fields.";
      eventFormError.classList.remove("hidden");
      return;
    }

    // Start time check
    const startDate = new Date(dateVal);
    const now = new Date();
    // Allow a small 3-minute grace period for click timing difference
    if (startDate < new Date(now.getTime() - 180000)) {
      eventFormError.textContent = "Event start time cannot be in the past.";
      eventFormError.classList.remove("hidden");
      return;
    }

    // Extract duration & compute end date
    const durationSelect = eventDurationSelect.value;
    let durationMinutes = parseInt(durationSelect, 10);
    if (durationSelect === "custom") {
      durationMinutes = parseInt(customDurationInput.value, 10);
    }

    if (isNaN(durationMinutes) || durationMinutes <= 0) {
      eventFormError.textContent = "Please enter a valid event duration.";
      eventFormError.classList.remove("hidden");
      return;
    }

    // Compute local ISO end date
    const endDate = new Date(startDate.getTime() + durationMinutes * 60000);
    const endDateVal = new Date(endDate.getTime() - endDate.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    
    const payload = {
      type: "event",
      name: title,
      description: desc,
      date: dateVal,
      end_date: endDateVal,
      lat: lat,
      lng: lng,
      campus_id: CAMPUS_ID
    };
    
    try {
      const res = await fetch("/api/pin/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) {
        let errMsg = "Failed to publish event.";
        try {
          const err = await res.json();
          errMsg = err.error || errMsg;
        } catch {
          const rawText = await res.text();
          if (rawText && rawText.length < 200) {
            errMsg = rawText;
          }
        }
        throw new Error(errMsg);
      }
      
      const newPin = await res.json();
      pins.push(newPin);

      eventCreationForm.reset();
      customDurationGroup.classList.add("hidden");
      closeModal(eventModalOverlay);
      exitPlacementMode();
      renderEventsList();
      openSidebar();
    } catch (err) {
      eventFormError.textContent = err.message;
      eventFormError.classList.remove("hidden");
    }
  });

    // Submit Create Campus Location Pin (Admin only)
  if (pinCreationForm) {
    pinCreationForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      pinFormError.classList.add("hidden");
      pinFormError.textContent = "";
      
      const type = document.querySelector('input[name="pinType"]:checked').value;
      const name = document.getElementById("pinName").value.trim();
      const desc = document.getElementById("pinDescription").value.trim();
      
      const latVal = document.getElementById("pinLat").value;
      const lngVal = document.getElementById("pinLng").value;
      const lat = latVal !== "" ? parseFloat(latVal) : null;
      const lng = lngVal !== "" ? parseFloat(lngVal) : null;
      
      if (!name) {
        pinFormError.textContent = "Name is required.";
        pinFormError.classList.remove("hidden");
        return;
      }
      
      if (type !== "club" && (lat === null || lng === null || isNaN(lat) || isNaN(lng))) {
        pinFormError.textContent = "Location is required on map for offices.";
        pinFormError.classList.remove("hidden");
        return;
      }
      
      const payload = {
        type: type,
        name: name,
        description: desc,
        lat: lat,
        lng: lng,
        campus_id: CAMPUS_ID
      };
      
      try {
        const res = await fetch("/api/pin/add", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        
        if (!res.ok) {
          let errMsg = "Failed to add location pin.";
          try {
            const resCloned = res.clone();
            const err = await resCloned.json();
            errMsg = err.error || errMsg;
          } catch {
            const rawText = await res.text();
            if (rawText && rawText.length < 200) {
              errMsg = rawText;
            }
          }
          throw new Error(errMsg);
        }
        
        const newPin = await res.json();
        pins.push(newPin);
 
        pinCreationForm.reset();
        closeModal(pinModalOverlay);
        exitPlacementMode();
        prependLegacyCard(newPin);
      } catch (err) {
        pinFormError.textContent = err.message;
        pinFormError.classList.remove("hidden");
      }
    });
  }

  // Radio button toggles in admin modal updates title label nicely
  const pinRadios = document.querySelectorAll('input[name="pinType"]');
  pinRadios.forEach(radio => {
    radio.addEventListener("change", function() {
      const label = document.getElementById("pinNameLabel");
      const nameInput = document.getElementById("pinName");
      if (this.value === "club") {
        label.textContent = "Club Name *";
        nameInput.placeholder = "e.g. Robotics Club";
      } else {
        label.textContent = "Office Name *";
        nameInput.placeholder = "e.g. Admission Office";
      }
      updateModalLocationStatus();
    });
  });

  // Cancel modals
  btnCancelEventModal.addEventListener("click", () => closeModal(eventModalOverlay));
  btnCloseEventModal.addEventListener("click", () => closeModal(eventModalOverlay));
  if (btnCancelPinModal) btnCancelPinModal.addEventListener("click", () => closeModal(pinModalOverlay));
  if (btnClosePinModal) btnClosePinModal.addEventListener("click", () => closeModal(pinModalOverlay));

  if (btnSelectLocationOnMap) {
    btnSelectLocationOnMap.addEventListener("click", (e) => {
      e.stopPropagation();
      pinModalOverlay.classList.add("hidden");
      enterPlacementMode("pin");
    });
  }

  if (btnClearPinLocation) {
    btnClearPinLocation.addEventListener("click", (e) => {
      e.stopPropagation();
      if (pinLatInput) pinLatInput.value = "";
      if (pinLngInput) pinLngInput.value = "";
      removeTempMarker();
      updateModalLocationStatus();
    });
  }

  if (btnColumnAddClub) {
    btnColumnAddClub.addEventListener("click", (e) => {
      e.stopPropagation();
      if (pinLatInput) pinLatInput.value = "";
      if (pinLngInput) pinLngInput.value = "";
      removeTempMarker();
      const clubRadio = document.querySelector('input[name="pinType"][value="club"]');
      if (clubRadio) {
        clubRadio.checked = true;
        clubRadio.dispatchEvent(new Event("change"));
      }
      updateModalLocationStatus();
      openModal(pinModalOverlay);
    });
  }

  if (btnColumnAddOffice) {
    btnColumnAddOffice.addEventListener("click", (e) => {
      e.stopPropagation();
      if (pinLatInput) pinLatInput.value = "";
      if (pinLngInput) pinLngInput.value = "";
      removeTempMarker();
      const officeRadio = document.querySelector('input[name="pinType"][value="office"]');
      if (officeRadio) {
        officeRadio.checked = true;
        officeRadio.dispatchEvent(new Event("change"));
      }
      updateModalLocationStatus();
      openModal(pinModalOverlay);
    });
  }

  // ── Filters Toggling ──────────────────────────────────────────
  const filterTabs = document.querySelectorAll(".filter-tab");
  filterTabs.forEach((tab) => {
    tab.addEventListener("click", function () {
      filterTabs.forEach((t) => t.classList.remove("active"));
      this.classList.add("active");
      
      activeFilter = this.dataset.filter;
      closePopover();
      renderAllPins();
    });
  });

  // ── Sidebar Slide-out Panel Logic ─────────────────────────────
  function openSidebar() {
    eventsSidebar.classList.remove("collapsed");
    if (btnToggleEvents) btnToggleEvents.classList.add("active");
    
    // Update URL dynamically to ?view=events
    const url = new URL(window.location.href);
    if (url.searchParams.get("view") !== "events") {
      url.searchParams.set("view", "events");
      window.history.pushState({}, "", url.pathname + url.search);
      if (typeof window.updateNavActiveStates === "function") {
        window.updateNavActiveStates();
      }
    }
    
    // If the active filter hides events (i.e. is not 'all' and not 'event')
    if (activeFilter !== "all" && activeFilter !== "event") {
      const eventFilterTab = document.querySelector('.filter-tab[data-filter="event"]');
      if (eventFilterTab) {
        eventFilterTab.click();
      }
    }
    
    // Animate event pins (pulse them to get bigger and smaller twice)
    setTimeout(() => {
      const eventPins = document.querySelectorAll(".pin-event");
      eventPins.forEach((pin) => {
        pin.classList.add("pulsing-appeal");
        // Clear class after animation finishes so it can be re-triggered
        pin.addEventListener("animationend", function handler() {
          pin.classList.remove("pulsing-appeal");
          pin.removeEventListener("animationend", handler);
        });
      });
    }, 400);
  }

  function closeSidebar() {
    eventsSidebar.classList.add("collapsed");
    if (btnToggleEvents) btnToggleEvents.classList.remove("active");
    
    // Update URL dynamically to remove ?view=events
    const url = new URL(window.location.href);
    if (url.searchParams.has("view")) {
      url.searchParams.delete("view");
      window.history.pushState({}, "", url.pathname + url.search);
      if (typeof window.updateNavActiveStates === "function") {
        window.updateNavActiveStates();
      }
    }
  }

  function toggleSidebar() {
    if (eventsSidebar.classList.contains("collapsed")) {
      openSidebar();
    } else {
      closeSidebar();
    }
  }

  if (btnToggleEvents) {
    btnToggleEvents.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleSidebar();
    });
  }
  
  btnCloseSidebar.addEventListener("click", (e) => {
    e.stopPropagation();
    closeSidebar();
  });

  // Listen for back/forward navigation
  window.addEventListener("popstate", () => {
    if (typeof window.updateNavActiveStates === "function") {
      window.updateNavActiveStates();
    }
    
    const params = new URLSearchParams(window.location.search);
    if (params.get("view") === "events") {
      eventsSidebar.classList.remove("collapsed");
      if (btnToggleEvents) btnToggleEvents.classList.add("active");
    } else {
      eventsSidebar.classList.add("collapsed");
      if (btnToggleEvents) btnToggleEvents.classList.remove("active");
    }
  });

  // Intercept left sidebar navigation link clicks when we are already on the map page
  document.querySelectorAll(".base-nav-item").forEach(link => {
    if (link.href) {
      try {
        const linkUrl = new URL(link.href, window.location.origin);
        const currentUrl = new URL(window.location.href, window.location.origin);
        if (linkUrl.pathname === currentUrl.pathname) {
          link.addEventListener("click", (e) => {
            e.preventDefault();
            const linkView = linkUrl.searchParams.get("view");
            if (linkView === "events") {
              openSidebar();
            } else {
              closeSidebar();
            }
          });
        }
      } catch (err) {
        console.error("Error parsing link URL in campus_map.js:", err);
      }
    }
  });

  // ── Action Buttons for placement mode launch ───────────────────
  if (btnAddEvent) {
    btnAddEvent.addEventListener("click", (e) => {
      e.stopPropagation();
      enterPlacementMode("event");
    });
  }
  
  btnSidebarAddEvent.addEventListener("click", (e) => {
    e.stopPropagation();
    enterPlacementMode("event");
  });
  
  if (btnAddPin) {
    btnAddPin.addEventListener("click", (e) => {
      e.stopPropagation();
      enterPlacementMode("pin");
    });
  }

  // ── Helpers ──────────────────────────────────────────────────
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatEventDuration(startIso, endIso) {
    const start = new Date(startIso);
    const end = new Date(endIso);
    
    const optionsDate = { month: "short", day: "numeric" };
    const optionsTime = { hour: "2-digit", minute: "2-digit" };
    
    const startDateStr = start.toLocaleDateString("en-US", optionsDate);
    const startTimeStr = start.toLocaleTimeString("en-US", optionsTime);
    const endTimeStr = end.toLocaleTimeString("en-US", optionsTime);
    
    // Check if event finishes on the same day
    if (start.toDateString() === end.toDateString()) {
      return `${startDateStr}, ${startTimeStr} - ${endTimeStr}`;
    } else {
      const endDateStr = end.toLocaleDateString("en-US", optionsDate);
      return `${startDateStr} ${startTimeStr} - ${endDateStr} ${endTimeStr}`;
    }
  }

  // ── Boot ─────────────────────────────────────────────────────
  init();
});
