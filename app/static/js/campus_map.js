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
  let placementMode = "none"; // 'none', 'event', 'pin'
  let activeFilter = "all";
  let activePinEl = null;
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
  const pinYInput = document.getElementById("pinY");
  const pinXInput = document.getElementById("pinX");

  function updateModalLocationStatus() {
    if (!pinLocationStatusText) return;
    let y = "";
    if (pinYInput) {
      y = pinYInput.value;
    }
    let x = "";
    if (pinXInput) {
      x = pinXInput.value;
    }
    const selectedRadio = document.querySelector('input[name="type"]:checked');
    let type = "club";
    if (selectedRadio) {
      type = selectedRadio.value;
    }
    
    if (y && x) {
      pinLocationStatusText.textContent = `📍 Selected: ${parseFloat(x).toFixed(1)}%, ${parseFloat(y).toFixed(1)}%`;
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

  // ── Init ─────────────────────────────────────────────────────
  function init() {
    // 1. Hook up click listeners to existing DOM pins
    document.querySelectorAll(".blueprint-pin").forEach(pinEl => {
      pinEl.addEventListener("click", (e) => {
        e.stopPropagation();
        showPopoverFromEl(pinEl);
      });
    });

    // 2. Hook up hover & toggle listeners to existing sidebar cards
    document.querySelectorAll(".event-sidebar-card").forEach(card => {
      const eventId = card.dataset.id;
      
      card.addEventListener("mouseenter", () => {
        highlightPin("event", eventId);
      });
      card.addEventListener("mouseleave", () => {
        unhighlightPin("event", eventId);
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
          const pinEl = document.querySelector(`.blueprint-pin[data-type="event"][data-id="${eventId}"]`);
          if (pinEl) {
            showPopoverFromEl(pinEl);
            pinEl.classList.add("pulsing-appeal");
            setTimeout(() => pinEl.classList.remove("pulsing-appeal"), 1500);
          }
        } else {
          closePopover();
        }
      });
    });
    
    // Check URL parameters for starting state
    const params = new URLSearchParams(window.location.search);
    if (params.get("view") === "events") {
      openSidebar();
    } else {
      // By default collapse the sidebar
      eventsSidebar.classList.add("collapsed");
    }
  }

  // ── Custom Popover / Tooltip Logic ────────────────────────────
  function showPopoverFromEl(pinEl) {
    closePopover();
    
    const popover = pinEl.querySelector(".pin-popover");
    if (!popover) return;
    
    // Elevate clicked pin's z-index so popover stays on top
    pinEl.style.zIndex = "600";
    
    popover.classList.add("visible");
    activePinEl = pinEl;
  }

  function closePopover() {
    if (activePinEl) {
      const popover = activePinEl.querySelector(".pin-popover");
      if (popover) {
        popover.classList.remove("visible");
      }
      activePinEl.style.zIndex = "";
      activePinEl = null;
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
  function deletePin(deleteUrl) {
    if (confirm("Remove this location pin?")) {
      const form = document.createElement("form");
      form.action = deleteUrl;
      form.method = "POST";
      document.body.appendChild(form);
      form.submit();
    }
  }
  window.deletePin = deletePin;

  // ── Interactive Location Choosing ─────────────────────────────
  function enterPlacementMode(type) {
    closePopover();
    placementMode = type;
    
    // Enter visual selection mode: center card, show gold caption & full-viewport overlay
    blueprintCard.classList.add("active-placement");
    blueprintCanvasWrapper.classList.add("choosing-location");
    blueprintBlurOverlay.classList.remove("hidden");
    placementGoldCaption.classList.remove("hidden");
    document.body.classList.add("active-placement-mode");

    // Dynamic caption text based on placement type
    if (placementGoldCaption) {
      if (type === "event") {
        placementGoldCaption.textContent = "Choose the event location by clicking on the blueprint map below...";
      } else if (type === "pin") {
        const selectedRadio = document.querySelector('input[name="type"]:checked');
        let subType = "location";
        if (selectedRadio) {
          subType = selectedRadio.value;
        }
        placementGoldCaption.textContent = `Choose the ${subType} location by clicking on the blueprint map below...`;
      } else {
        placementGoldCaption.textContent = "Choose the location by clicking on the blueprint map below...";
      }
    }
    
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
    document.body.classList.remove("active-placement-mode");
    
    // Clear inline display style set during placement mode
    const pinsEls = document.querySelectorAll(".blueprint-pin");
    pinsEls.forEach(p => p.style.display = "");
    
    // Restore all pins visibility based on filter
    updatePinVisibility();
    removeTempMarker();
  }

  function removeTempMarker() {
    if (tempMarker) {
      tempMarker.remove();
      tempMarker = null;
    }
  }

  function updatePinVisibility() {
    const pinsEls = document.querySelectorAll(".blueprint-pin");
    pinsEls.forEach(pinEl => {
      if (activeFilter === "all" || pinEl.dataset.type === activeFilter) {
        pinEl.classList.remove("filtered-out");
      } else {
        pinEl.classList.add("filtered-out");
      }
    });
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
        document.getElementById("eventY").value = yPercent;
        document.getElementById("eventX").value = xPercent;
        enforceMinDateLimit();
        openModal(eventModalOverlay);
      } else if (placementMode === "pin") {
        document.getElementById("pinY").value = yPercent;
        document.getElementById("pinX").value = xPercent;
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
  eventCreationForm.addEventListener("submit", (e) => {
    eventFormError.classList.add("hidden");
    eventFormError.textContent = "";
    
    const title = document.getElementById("eventTitle").value.trim();
    const dateVal = eventDateInput.value; // start date string
    const yVal = document.getElementById("eventY").value;
    const xVal = document.getElementById("eventX").value;
    let y = NaN;
    if (yVal !== "") {
      y = parseFloat(yVal);
    }
    let x = NaN;
    if (xVal !== "") {
      x = parseFloat(xVal);
    }

    if (!title || !dateVal || isNaN(x) || isNaN(y)) {
      e.preventDefault();
      eventFormError.textContent = "Please select a location on the map and fill in all fields.";
      eventFormError.classList.remove("hidden");
      return;
    }

    // Start time check
    const startDate = new Date(dateVal);
    const now = new Date();
    // Allow a small 3-minute grace period for clock drift
    if (startDate < new Date(now.getTime() - 180000)) {
      e.preventDefault();
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
      e.preventDefault();
      eventFormError.textContent = "Please enter a valid event duration.";
      eventFormError.classList.remove("hidden");
      return;
    }

    // Compute UTC end date
    const endDate = new Date(startDate.getTime() + durationMinutes * 60000);
    
    // Set hidden fields for standard POST submission in UTC format
    document.getElementById("eventDateUTC").value = startDate.toISOString();
    document.getElementById("eventEndDateUTC").value = endDate.toISOString();
  });

  // Submit Create Campus Location Pin (Admin only)
  if (pinCreationForm) {
    pinCreationForm.addEventListener("submit", (e) => {
      pinFormError.classList.add("hidden");
      pinFormError.textContent = "";
      
      const typeEl = document.querySelector('input[name="type"]:checked');
      let type = "club";
      if (typeEl) {
        type = typeEl.value;
      }
      const name = document.getElementById("pinName").value.trim();
      
      const yVal = document.getElementById("pinY").value;
      const xVal = document.getElementById("pinX").value;
      let y = null;
      if (yVal !== "") {
        y = parseFloat(yVal);
      }
      let x = null;
      if (xVal !== "") {
        x = parseFloat(xVal);
      }
      
      if (!name) {
        e.preventDefault();
        pinFormError.textContent = "Name is required.";
        pinFormError.classList.remove("hidden");
        return;
      }
      
      if (type !== "club" && (y === null || x === null || isNaN(y) || isNaN(x))) {
        e.preventDefault();
        pinFormError.textContent = "Location is required on map for offices.";
        pinFormError.classList.remove("hidden");
        return;
      }
    });
  }

  // Radio button toggles in admin modal updates title label nicely
  const pinRadios = document.querySelectorAll('input[name="type"]');
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
      if (pinYInput) pinYInput.value = "";
      if (pinXInput) pinXInput.value = "";
      removeTempMarker();
      updateModalLocationStatus();
    });
  }

  if (btnColumnAddClub) {
    btnColumnAddClub.addEventListener("click", (e) => {
      e.stopPropagation();
      if (pinYInput) pinYInput.value = "";
      if (pinXInput) pinXInput.value = "";
      removeTempMarker();
      const clubRadio = document.querySelector('input[name="type"][value="club"]');
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
      if (pinYInput) pinYInput.value = "";
      if (pinXInput) pinXInput.value = "";
      removeTempMarker();
      const officeRadio = document.querySelector('input[name="type"][value="office"]');
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
      updatePinVisibility();
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

  // ── Boot ─────────────────────────────────────────────────────
  init();
});
