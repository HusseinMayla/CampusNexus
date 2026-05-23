/* ═══════════════════════════════════════════════════════════════
   LearnHive — map.js
   ════════════════════════════════════════════════════════════════ */

// ── State ──────────────────────────────────────────────────────
let map;
const markers      = {};
let placementMode  = false;
let tempMarker     = null;
let pendingLatLng  = null;
let currentFilter  = 'all';
let allPins        = [];
let searchedCenter = null;

// ── Config from DOM ────────────────────────────────────────────
const cfg       = document.getElementById('map-config').dataset;
const CAMPUS_ID = cfg.campusId;
const IS_ADMIN  = cfg.isAdmin === 'true';
const CAMPUS_NAME = cfg.campusName;
const centerLat = cfg.centerLat ? parseFloat(cfg.centerLat) : null;
const centerLng = cfg.centerLng ? parseFloat(cfg.centerLng) : null;

// ── SVG icons per type ─────────────────────────────────────────
const ICONS = {
  club: `<svg viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>`,
  office: `<svg viewBox="0 0 24 24"><path d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10zm-2-8h-2v2h2v-2zm0 4h-2v2h2v-2z"/></svg>`,
  event: `<svg viewBox="0 0 24 24"><path d="M17 12h-5v5h5v-5zM16 1v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2h-1V1h-2zm3 18H5V8h14v11z"/></svg>`,
};

// ── Build custom Leaflet DivIcon ───────────────────────────────
function makeIcon(type) {
  return L.divIcon({
    className: '',
    html: `<div class="map-marker map-marker-${type}">${ICONS[type]}</div>`,
    iconSize:    [34, 34],
    iconAnchor:  [12, 34],
    popupAnchor: [5, -34],
  });
}

// ── Init map ───────────────────────────────────────────────────
function initMap() {
  const defaultCenter = (centerLat && centerLng) ? [centerLat, centerLng] : [20, 0];
  const defaultZoom   = (centerLat && centerLng) ? 16 : 2;

  map = L.map('map', { zoomControl: false }).setView(defaultCenter, defaultZoom);

  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(map);

  L.control.zoom({ position: 'bottomright' }).addTo(map);

  fetchPins();

  if (IS_ADMIN) setupAdminControls();

  setupFilters();
  setupPinListClicks();
}

// ── Fetch and render all pins ──────────────────────────────────
async function fetchPins() {
  try {
    const res  = await fetch(`/api/map-data/${CAMPUS_ID}`);
    const pins = await res.json();
    allPins = pins;
    pins.forEach(renderPin);
    updatePinList();
  } catch (err) {
    console.error('Failed to fetch pins:', err);
  }
}

function renderPin(pin) {
  const marker = L.marker([pin.lat, pin.lng], { icon: makeIcon(pin.type) });
  marker.bindPopup(buildPopup(pin), { className: 'lh-popup', maxWidth: 260 });
  marker.pinData = pin;
  marker.addTo(map);
  markers[`${pin.type}-${pin.id}`] = marker;
}

// ── Build popup HTML ───────────────────────────────────────────
function buildPopup(pin) {
  const dateRow = (pin.type === 'event' && pin.date)
    ? `<p class="popup-date">📅 ${formatDate(pin.date)}</p>`
    : '';

  const deleteBtn = IS_ADMIN
    ? `<button class="popup-delete" data-type="${pin.type}" data-id="${pin.id}">Remove pin</button>`
    : '';

  return `
    <div class="popup-type-bar popup-type-bar-${pin.type}"></div>
    <div class="popup-content">
      <h4 class="popup-title">${escapeHtml(pin.name)}</h4>
      ${dateRow}
      <p class="popup-desc">${escapeHtml(pin.description)}</p>
      ${deleteBtn}
    </div>`;
}

// ── Event delegation for popup delete buttons ──────────────────
document.getElementById('map').addEventListener('click', function (e) {
  if (!e.target.classList.contains('popup-delete')) return;
  const type = e.target.dataset.type;
  const id   = parseInt(e.target.dataset.id, 10);
  deletePin(type, id);
});

// ── Admin controls ─────────────────────────────────────────────
function setupAdminControls() {
  document.getElementById('addPinBtn').addEventListener('click', togglePlacementMode);
  document.getElementById('pinFormClose').addEventListener('click', cancelPlacement);
  document.getElementById('pinCancelBtn').addEventListener('click', cancelPlacement);
  document.getElementById('pinSaveBtn').addEventListener('click', savePin);

  document.querySelectorAll('input[name="pinType"]').forEach(radio => {
    radio.addEventListener('change', function () {
      document.getElementById('eventDateGroup')
        .classList.toggle('hidden', this.value !== 'event');
    });
  });

  document.getElementById('searchBtn').addEventListener('click', searchCampus);
  document.getElementById('campusSearch').addEventListener('keydown', e => {
    if (e.key === 'Enter') searchCampus();
  });

  document.getElementById('setCenterBtn').addEventListener('click', saveCampusCenter);

  map.on('click', function (e) {
    if (!placementMode) return;
    pendingLatLng = e.latlng;

    if (tempMarker) map.removeLayer(tempMarker);
    tempMarker = L.marker(e.latlng, {
      icon: L.divIcon({
        className: '',
        html: '<div class="temp-marker-inner"></div>',
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      }),
    }).addTo(map);

    document.getElementById('pinFormPanel').classList.add('open');
  });
}

function togglePlacementMode() {
  placementMode = !placementMode;
  const btn  = document.getElementById('addPinBtn');
  const wrap = document.querySelector('.map-wrap');
  btn.classList.toggle('active', placementMode);
  btn.textContent = placementMode ? '✕ Cancel' : '+ Add Pin';
  wrap.classList.toggle('placement-cursor', placementMode);

  if (!placementMode) {
    document.getElementById('pinFormPanel').classList.remove('open');
    if (tempMarker) { map.removeLayer(tempMarker); tempMarker = null; }
    pendingLatLng = null;
  }
}

function cancelPlacement() {
  if (placementMode) togglePlacementMode();
  clearPinForm();
}

async function savePin() {
  const name  = document.getElementById('pinName').value.trim();
  const desc  = document.getElementById('pinDesc').value.trim();
  const type  = document.querySelector('input[name="pinType"]:checked').value;
  const date  = document.getElementById('pinDate').value;
  const errEl = document.getElementById('pinError');

  errEl.textContent = '';

  if (!name)          { errEl.textContent = 'Name is required.'; return; }
  if (!pendingLatLng) { errEl.textContent = 'Click on the map to place the pin first.'; return; }
  if (type === 'event' && !date) { errEl.textContent = 'Please select a date for the event.'; return; }

  const payload = {
    type, name, description: desc,
    lat:       pendingLatLng.lat,
    lng:       pendingLatLng.lng,
    campus_id: CAMPUS_ID,
    date:      date || null,
  };

  try {
    const res = await fetch('/api/pin/add', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });

    if (res.ok) {
      const newPin = await res.json();
      if (tempMarker) { map.removeLayer(tempMarker); tempMarker = null; }
      allPins.push(newPin);
      renderPin(newPin);
      updatePinList();
      cancelPlacement();
    } else {
      const err = await res.json();
      errEl.textContent = err.error || 'Failed to save pin.';
    }
  } catch {
    errEl.textContent = 'Network error. Please try again.';
  }
}

function clearPinForm() {
  document.getElementById('pinName').value  = '';
  document.getElementById('pinDesc').value  = '';
  document.getElementById('pinDate').value  = '';
  document.getElementById('pinError').textContent = '';
  document.querySelector('input[name="pinType"][value="club"]').checked = true;
  document.getElementById('eventDateGroup').classList.add('hidden');
}

async function deletePin(type, id) {
  if (!confirm(`Remove this ${type}?`)) return;

  try {
    const res = await fetch(`/api/pin/delete/${type}/${id}`, { method: 'DELETE' });
    if (res.ok) {
      const key = `${type}-${id}`;
      if (markers[key]) { map.removeLayer(markers[key]); delete markers[key]; }
      map.closePopup();
      allPins = allPins.filter(p => !(p.type === type && p.id === id));
      updatePinList();
    }
  } catch {
    alert('Failed to remove pin. Please try again.');
  }
}

// ── Search / Nominatim geocoding ───────────────────────────────
async function searchCampus() {
  const query     = document.getElementById('campusSearch').value.trim();
  const hintEl    = document.getElementById('searchHint');
  const centerBtn = document.getElementById('setCenterBtn');

  if (!query) return;
  hintEl.textContent = 'Searching…';
  centerBtn.classList.add('hidden');

  try {
    const res     = await fetch(
      `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1`,
      { headers: { 'Accept-Language': 'en' } }
    );
    const results = await res.json();

    if (!results.length) {
      hintEl.textContent = 'Location not found. Try a more specific name.';
      return;
    }

    const { lat, lon, display_name } = results[0];
    searchedCenter = { lat: parseFloat(lat), lng: parseFloat(lon) };
    map.flyTo([searchedCenter.lat, searchedCenter.lng], 16, { duration: 1.5 });

    const shortName = display_name.split(',').slice(0, 2).join(',');
    hintEl.textContent = `Found: ${shortName}`;
    centerBtn.classList.remove('hidden');
  } catch {
    hintEl.textContent = 'Search failed. Check your connection.';
  }
}

async function saveCampusCenter() {
  if (!searchedCenter) return;
  const btn = document.getElementById('setCenterBtn');

  try {
    const res = await fetch('/api/campus/set-center', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ campus_id: CAMPUS_ID, ...searchedCenter }),
    });
    if (res.ok) {
      btn.textContent  = '✓ Center Saved';
      btn.style.cursor = 'default';
      setTimeout(() => {
        btn.classList.add('hidden');
        btn.textContent  = 'Set as Campus Center';
        btn.style.cursor = '';
      }, 2500);
    }
  } catch {
    document.getElementById('searchHint').textContent = 'Failed to save. Try again.';
  }
}

// ── Filter pins ────────────────────────────────────────────────
function setupFilters() {
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      currentFilter = this.dataset.filter;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      applyFilter();
    });
  });
}

function applyFilter() {
  Object.entries(markers).forEach(([key, marker]) => {
    const type = marker.pinData.type;
    const show = currentFilter === 'all' || type === currentFilter;
    if (show && !map.hasLayer(marker)) marker.addTo(map);
    if (!show && map.hasLayer(marker)) map.removeLayer(marker);
  });
}

// ── Sidebar pin list ───────────────────────────────────────────
function updatePinList() {
  const list = document.getElementById('pinList');
  list.innerHTML = '';

  if (!allPins.length) {
    const li = document.createElement('li');
    li.className = 'pin-list-empty';
    li.textContent = 'No pins yet.';
    list.appendChild(li);
    return;
  }

  allPins.forEach(pin => {
    const li  = document.createElement('li');
    li.className = 'pin-list-item';
    li.dataset.type = pin.type;
    li.dataset.id   = pin.id;

    const dot = document.createElement('span');
    dot.className = `pin-list-dot dot-${pin.type}`;

    const name = document.createElement('span');
    name.textContent = pin.name;

    li.appendChild(dot);
    li.appendChild(name);
    list.appendChild(li);
  });
}

function setupPinListClicks() {
  document.getElementById('pinList').addEventListener('click', function (e) {
    const item = e.target.closest('.pin-list-item');
    if (!item) return;
    const key    = `${item.dataset.type}-${item.dataset.id}`;
    const marker = markers[key];
    if (!marker) return;
    map.flyTo(marker.getLatLng(), 18, { duration: 0.8 });
    marker.openPopup();
  });
}

// ── Helpers ────────────────────────────────────────────────────
function formatDate(isoStr) {
  return new Date(isoStr).toLocaleString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Boot ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', initMap);
