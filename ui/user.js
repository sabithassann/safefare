/**
 * SafeFare Commuter Portal - User Frontend Logic
 */

const API_BASE = '/api/v1';

let activeProofUrl = null;
let allAvailableRoutes = [];

// DOM Elements
const elements = {
  // Search Form
  form: document.getElementById('commuterSearchForm'),
  sourceInput: document.getElementById('userSourceInput'),
  destInput: document.getElementById('userDestInput'),
  routeSelect: document.getElementById('userRouteSelect'),
  sourceSuggestions: document.getElementById('userSourceSuggestions'),
  destSuggestions: document.getElementById('userDestSuggestions'),
  btnClearSource: document.getElementById('btnClearSource'),
  btnClearDest: document.getElementById('btnClearDest'),
  btnSwap: document.getElementById('btnSwapStops'),
  btnCalculate: document.getElementById('btnCalculateFare'),
  quickChips: document.querySelectorAll('.quick-chip'),

  // Results
  resultContainer: document.getElementById('fareResultContainer'),
  resultRouteTitle: document.getElementById('resultRouteTitle'),
  resultFareAmount: document.getElementById('resultFareAmount'),
  resultDistance: document.getElementById('resultDistance'),
  resultStudentFare: document.getElementById('resultStudentFare'),
  resultFormula: document.getElementById('resultFormula'),
  btnOpenOfficialProof: document.getElementById('btnOpenOfficialProof'),

  // Routes Catalog
  routesGrid: document.getElementById('userRoutesGrid'),

  // Modals
  proofModal: document.getElementById('userProofModal'),
  proofTitle: document.getElementById('userProofModalTitle'),
  proofImg: document.getElementById('userProofImg'),
  proofLoading: document.getElementById('userProofLoading'),
  btnCloseProof: document.getElementById('btnCloseUserProof'),
  btnCloseProof2: document.getElementById('btnCloseUserProof2'),

  routeDetailModal: document.getElementById('routeDetailModal'),
  routeDetailTitle: document.getElementById('routeDetailTitle'),
  routeDetailSubtitle: document.getElementById('routeDetailSubtitle'),
  routeDetailStopsList: document.getElementById('routeDetailStopsList'),
  btnCloseRouteDetail: document.getElementById('btnCloseRouteDetail'),
  btnCloseRouteDetail2: document.getElementById('btnCloseRouteDetail2'),

  toastContainer: document.getElementById('userToastContainer')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  initEventListeners();
  loadRoutesCatalog();
});

function initEventListeners() {
  // Autocomplete setup
  setupAutocomplete(elements.sourceInput, elements.sourceSuggestions, elements.btnClearSource);
  setupAutocomplete(elements.destInput, elements.destSuggestions, elements.btnClearDest);

  // Swap button
  elements.btnSwap.addEventListener('click', () => {
    const tmp = elements.sourceInput.value;
    elements.sourceInput.value = elements.destInput.value;
    elements.destInput.value = tmp;
    toggleClearButton(elements.sourceInput, elements.btnClearSource);
    toggleClearButton(elements.destInput, elements.btnClearDest);
    hideAllSuggestions();
    if (elements.sourceInput.value && elements.destInput.value) {
      elements.form.dispatchEvent(new Event('submit'));
    }
  });

  // Quick chips
  elements.quickChips.forEach(chip => {
    chip.addEventListener('click', () => {
      elements.sourceInput.value = chip.dataset.src;
      elements.destInput.value = chip.dataset.dest;
      toggleClearButton(elements.sourceInput, elements.btnClearSource);
      toggleClearButton(elements.destInput, elements.btnClearDest);
      hideAllSuggestions();
      elements.form.dispatchEvent(new Event('submit'));
    });
  });

  // Search submission
  elements.form.addEventListener('submit', handleFareSearch);

  // View proof action
  elements.btnOpenOfficialProof.addEventListener('click', openProofModal);

  // Close modals
  elements.btnCloseProof.addEventListener('click', () => elements.proofModal.classList.add('hidden'));
  elements.btnCloseProof2.addEventListener('click', () => elements.proofModal.classList.add('hidden'));
  elements.btnCloseRouteDetail.addEventListener('click', () => elements.routeDetailModal.classList.add('hidden'));
  elements.btnCloseRouteDetail2.addEventListener('click', () => elements.routeDetailModal.classList.add('hidden'));

  // Close dropdowns on outside click
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.autocomplete-wrapper')) {
      hideAllSuggestions();
    }
  });
}

function setupAutocomplete(inputEl, dropdownEl, clearBtn) {
  let debounceTimer = null;

  inputEl.addEventListener('input', () => {
    toggleClearButton(inputEl, clearBtn);
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      fetchStopsAndSuggest(inputEl, dropdownEl);
    }, 150);
  });

  inputEl.addEventListener('focus', () => {
    fetchStopsAndSuggest(inputEl, dropdownEl);
  });

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      inputEl.value = '';
      toggleClearButton(inputEl, clearBtn);
      dropdownEl.classList.add('hidden');
      inputEl.focus();
    });
  }
}

function toggleClearButton(inputEl, clearBtn) {
  if (!clearBtn) return;
  if (inputEl.value.trim().length > 0) {
    clearBtn.classList.remove('hidden');
  } else {
    clearBtn.classList.add('hidden');
  }
}

async function fetchStopsAndSuggest(inputEl, dropdownEl) {
  const query = inputEl.value.trim();
  try {
    const url = query ? `${API_BASE}/fares/stops?q=${encodeURIComponent(query)}` : `${API_BASE}/fares/stops`;
    const res = await fetch(url);
    if (!res.ok) return;
    const stops = await res.json();

    if (stops.length === 0) {
      dropdownEl.innerHTML = '<div class="suggestion-item no-match">No matching stop found</div>';
      dropdownEl.classList.remove('hidden');
      return;
    }

    dropdownEl.innerHTML = stops.map(stop => `
      <div class="suggestion-item" data-stop="${escapeHtml(stop)}">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a8 8 0 0 0-8 8c0 5.25 8 12 8 12s8-6.75 8-12a8 8 0 0 0-8-8z"></path><circle cx="12" cy="10" r="3"></circle></svg>
        <span>${escapeHtml(stop)}</span>
      </div>
    `).join('');

    dropdownEl.querySelectorAll('.suggestion-item[data-stop]').forEach(item => {
      item.addEventListener('click', () => {
        inputEl.value = item.dataset.stop;
        dropdownEl.classList.add('hidden');
        const clearBtn = inputEl.id === 'userSourceInput' ? elements.btnClearSource : elements.btnClearDest;
        toggleClearButton(inputEl, clearBtn);
      });
    });

    dropdownEl.classList.remove('hidden');
  } catch (err) {
    dropdownEl.classList.add('hidden');
  }
}

function hideAllSuggestions() {
  if (elements.sourceSuggestions) elements.sourceSuggestions.classList.add('hidden');
  if (elements.destSuggestions) elements.destSuggestions.classList.add('hidden');
}

// -------------------------------------------------------------
// Fare Calculation Search
// -------------------------------------------------------------
async function handleFareSearch(e) {
  e.preventDefault();
  const source = elements.sourceInput.value.trim();
  const destination = elements.destInput.value.trim();
  const selectedRoute = elements.routeSelect.value;

  if (!source || !destination) {
    showToast('Please specify both origin and destination stops.', 'error');
    return;
  }

  if (source.toLowerCase() === destination.toLowerCase()) {
    showToast('Origin and destination cannot be identical.', 'warning');
    return;
  }

  try {
    elements.btnCalculate.disabled = true;
    elements.btnCalculate.innerHTML = '<span class="spinner-inline"></span> Calculating Fare...';
    hideAllSuggestions();

    const payload = {
      source: source,
      destination: destination
    };
    if (selectedRoute) {
      payload.route_name = selectedRoute;
    }

    const res = await fetch(`${API_BASE}/fares/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Fare calculation failed.');
    }

    const data = await res.json();
    displayFareResult(data, source, destination);
    showToast('Official government fare found!', 'success');
  } catch (err) {
    elements.resultContainer.classList.add('hidden');
    showToast(err.message, 'error');
  } finally {
    elements.btnCalculate.disabled = false;
    elements.btnCalculate.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
      Calculate Government Fare
    `;
  }
}

function displayFareResult(data, reqSrc, reqDest) {
  elements.resultRouteTitle.textContent = `${data.source} ➔ ${data.destination}`;
  elements.resultFareAmount.textContent = Number(data.calculated_fare).toFixed(2);
  elements.resultDistance.textContent = data.distance_km ? `${Number(data.distance_km).toFixed(2)} km` : 'Direct Route Pair';
  
  const studentFare = Math.max(10, Math.ceil(data.calculated_fare / 2));
  elements.resultStudentFare.textContent = `৳ ${studentFare.toFixed(2)}`;

  elements.resultFormula.textContent = `Base: ৳2.50/km | Min Fare: ৳10.00`;

  activeProofUrl = data.chart_url;
  elements.resultContainer.classList.remove('hidden');

  // Smooth scroll to result
  elements.resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function openProofModal() {
  if (!activeProofUrl) {
    showToast('Official chart proof URL is not available.', 'warning');
    return;
  }

  elements.proofModal.classList.remove('hidden');
  elements.proofLoading.classList.remove('hidden');
  elements.proofImg.classList.add('hidden');

  elements.proofImg.src = activeProofUrl;
  elements.proofImg.onload = () => {
    elements.proofLoading.classList.add('hidden');
    elements.proofImg.classList.remove('hidden');
  };
  elements.proofImg.onerror = () => {
    elements.proofLoading.textContent = 'Failed to load official chart proof image.';
  };
}

// -------------------------------------------------------------
// Routes Catalog Loading
// -------------------------------------------------------------
async function loadRoutesCatalog() {
  try {
    const res = await fetch(`${API_BASE}/admin/routes`);
    if (!res.ok) throw new Error('Could not fetch routes list');
    const routes = await res.json();
    allAvailableRoutes = routes;

    // Populate route filter dropdown
    elements.routeSelect.innerHTML = '<option value="">All Registered Routes</option>' + 
      routes.map(r => `<option value="${escapeHtml(r.route_name)}">${escapeHtml(r.route_name)}</option>`).join('');

    if (routes.length === 0) {
      elements.routesGrid.innerHTML = '<div class="empty-stops-hint">No transit routes registered yet in SafeFare.</div>';
      return;
    }

    elements.routesGrid.innerHTML = routes.map(r => `
      <div class="user-route-card">
        <div class="route-card-top">
          <span class="route-permit-tag">${escapeHtml(r.route_number || 'Route')}</span>
          <span class="badge ${r.mapped_cells === r.total_cells ? 'badge-success' : 'badge-warning'}">
            ${r.mapped_cells}/${r.total_cells} Matrix Mapped
          </span>
        </div>
        <h3 class="route-card-title">${escapeHtml(r.route_name)}</h3>
        <div class="route-card-stats">
          <div class="route-stat-item">
            <span class="stat-num">${r.total_stops}</span>
            <span class="stat-label">Stops</span>
          </div>
          <div class="route-stat-item">
            <span class="stat-num">${r.total_cells}</span>
            <span class="stat-label">Fare Pairs</span>
          </div>
          <div class="route-stat-item">
            <span class="stat-num">৳${r.min_fare || '10'}</span>
            <span class="stat-label">Min Fare</span>
          </div>
        </div>
        <button type="button" class="btn btn-secondary btn-sm btn-block" onclick="viewRouteDetail('${r.route_id}')">
          View Route Checkpoints & Stops
        </button>
      </div>
    `).join('');

  } catch (err) {
    elements.routesGrid.innerHTML = `<div class="empty-stops-hint">Error loading routes catalog: ${err.message}</div>`;
  }
}

window.viewRouteDetail = async function(routeId) {
  try {
    const res = await fetch(`${API_BASE}/admin/routes/${routeId}`);
    if (!res.ok) throw new Error('Route not found');
    const route = await res.json();

    elements.routeDetailTitle.textContent = route.route_name;
    elements.routeDetailSubtitle.textContent = `Permit No: ${route.route_number || 'N/A'} | Rate: ৳${route.rate_per_km}/km | Min Fare: ৳${route.min_fare}`;

    elements.routeDetailStopsList.innerHTML = route.stops.map((stop, index) => `
      <div class="timeline-stop-item">
        <div class="stop-marker">${index + 1}</div>
        <div class="stop-info">
          <strong>${escapeHtml(stop.name)}</strong>
          <span class="stop-sub">Checkpoint ${index + 1} of ${route.stops.length}</span>
        </div>
      </div>
    `).join('');

    elements.routeDetailModal.classList.remove('hidden');
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// -------------------------------------------------------------
// Utilities
// -------------------------------------------------------------
function showToast(message, type = 'info') {
  if (!elements.toastContainer) return;
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${escapeHtml(message)}</span>`;
  elements.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
