/* ═══════════════════════════════════════════════════════════════
   LearnHive — campus_map.js
   ════════════════════════════════════════════════════════════════ */

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
      // Filter check
      if (activeFilter !== "all" && pin.type !== activeFilter) return;
      
      const pinEl = document.createElement("div");
      pinEl.className = `blueprint-pin pin-${pin.type}`;
      pinEl.style.left = `${pin.lng}%`;
      pinEl.style.top = `${pin.lat}%`;
      pinEl.dataset.type = pin.type;
      pinEl.dataset.id = pin.id;
      
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
      
      const isCreatorOrAdmin = event.is_creator || IS_ADMIN;
      const deleteBtn = isCreatorOrAdmin 
        ? `<button class="event-delete-btn" data-id="${event.id}">Delete</button>` 
        : "";

      card.innerHTML = `
        <div class="card-top">
          <h4>${escapeHtml(event.name)}</h4>
          ${deleteBtn}
        </div>
        <div class="event-time">
          <span>📅 ${formatEventDuration(event.date, event.end_date)}</span>
        </div>
        <p>${escapeHtml(event.description || "No description provided.")}</p>
        <div class="event-author">
          👤 Host: ${escapeHtml(event.creator_name || "Anonymous")}
        </div>
      `;
      
      // Micro-interactions: hover event card highlights map pin
      card.addEventListener("mouseenter", () => {
        highlightPin("event", event.id);
      });
      card.addEventListener("mouseleave", () => {
        unhighlightPin("event", event.id);
      });
      
      // Click event card flies tooltips/popovers on map
      card.addEventListener("click", () => {
        const pinEl = document.querySelector(`.blueprint-pin[data-type="event"][data-id="${event.id}"]`);
        if (pinEl) {
          showPopover(event, pinEl);
          // Highlight/Pulse pin on card select
          pinEl.classList.add("pulsing-appeal");
          setTimeout(() => pinEl.classList.remove("pulsing-appeal"), 1500);
        }
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

    popover.innerHTML = `
      <div class="popover-type-bar popover-bar-${pin.type}"></div>
      <h4 class="popover-title">${escapeHtml(pin.name)}</h4>
      ${metaHtml}
      <p class="popover-desc">${escapeHtml(pin.description || "No description provided.")}</p>
      ${deleteHtml}
    `;
    
    // Position popover relative to the pin
    pinEl.appendChild(popover);
    
    // Triggers layout calculation so transition opacity works smoothly
    popover.getBoundingClientRect();
    popover.classList.add("visible");
    
    activePopover = { popover, pinEl, pin };
    
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
      pinEl.style.transform = "translate(-50%, -50%) rotate(-45deg) scale(1.35)";
      pinEl.style.zIndex = "500";
    }
  }

  function unhighlightPin(type, id) {
    const pinEl = document.querySelector(`.blueprint-pin[data-type="${type}"][data-id="${id}"]`);
    if (pinEl) {
      pinEl.style.transform = "";
      pinEl.style.zIndex = "";
    }
  }

  // ── Delete Pin / Event ────────────────────────────────────────
  async function deletePin(type, id) {
    if (!confirm(`Are you sure you want to remove this ${type}?`)) return;
    
    try {
      const res = await fetch(`/api/pin/delete/${type}/${id}`, {
        method: "DELETE"
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Failed to delete");
      }
      
      closePopover();
      pins = pins.filter(p => !(p.type === type && p.id === id));
      renderAllPins();
      renderEventsList();
    } catch (err) {
      alert(err.message);
    }
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
      
      // Auto open events sidebar and pulse pins
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
      const lat = parseFloat(document.getElementById("pinLat").value);
      const lng = parseFloat(document.getElementById("pinLng").value);
      
      if (!name || isNaN(lat) || isNaN(lng)) {
        pinFormError.textContent = "Please fill in all required fields.";
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
    });
  });

  // Cancel modals
  btnCancelEventModal.addEventListener("click", () => closeModal(eventModalOverlay));
  btnCloseEventModal.addEventListener("click", () => closeModal(eventModalOverlay));
  if (btnCancelPinModal) btnCancelPinModal.addEventListener("click", () => closeModal(pinModalOverlay));
  if (btnClosePinModal) btnClosePinModal.addEventListener("click", () => closeModal(pinModalOverlay));

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
