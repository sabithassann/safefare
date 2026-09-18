/**
 * SafeFare Studio - Frontend Application Logic
 */

const API_BASE = '/api/v1';

// App State
const state = {
  currentRoute: null,
  activeCellId: null,
  activeDrawTarget: 'fare_box', // 'fare_box' | 'source_box' | 'destination_box'
  stops: [],
  zoom: 1.0,
  filter: 'all',
  searchQuery: '',
  isDrawing: false,
  drawStart: { x: 0, y: 0 },
  currentRect: null,
  imageNaturalWidth: 0,
  imageNaturalHeight: 0
};

// DOM Elements
const elements = {
  // Views
  step1View: document.getElementById('step1View'),
  step2View: document.getElementById('step2View'),
  
  // Header
  routeHeaderStats: document.getElementById('routeHeaderStats'),
  headerRouteTitle: document.getElementById('headerRouteTitle'),
  headerProgressBadge: document.getElementById('headerProgressBadge'),
  btnOpenRoutesDrawer: document.getElementById('btnOpenRoutesDrawer'),
  btnNewRoute: document.getElementById('btnNewRoute'),

  // Step 1 Elements
  routeInitForm: document.getElementById('routeInitForm'),
  routeName: document.getElementById('routeName'),
  routeNumber: document.getElementById('routeNumber'),
  ratePerKm: document.getElementById('ratePerKm'),
  minFare: document.getElementById('minFare'),
  pdfFileInput: document.getElementById('pdfFileInput'),
  pdfDropzone: document.getElementById('pdfDropzone'),
  uploadFilename: document.getElementById('uploadFilename'),
  newStopInput: document.getElementById('newStopInput'),
  btnAddStop: document.getElementById('btnAddStop'),
  btnPasteBulkStops: document.getElementById('btnPasteBulkStops'),
  btnLoadSampleStops: document.getElementById('btnLoadSampleStops'),
  stopsListContainer: document.getElementById('stopsListContainer'),
  stopsSummaryBadge: document.getElementById('stopsSummaryBadge'),
  stopsCountText: document.getElementById('stopsCountText'),
  pairsCountText: document.getElementById('pairsCountText'),
  btnSubmitStep1: document.getElementById('btnSubmitStep1'),

  // Step 2 Canvas
  canvasViewport: document.getElementById('canvasViewport'),
  canvasWrapper: document.getElementById('canvasWrapper'),
  chartImage: document.getElementById('chartImage'),
  interactiveCanvas: document.getElementById('interactiveCanvas'),
  activeCellInfo: document.getElementById('activeCellInfo'),
  coordsTracker: document.getElementById('coordsTracker'),
  zoomLevelDisplay: document.getElementById('zoomLevelDisplay'),
  btnZoomIn: document.getElementById('btnZoomIn'),
  btnZoomOut: document.getElementById('btnZoomOut'),
  btnResetZoom: document.getElementById('btnResetZoom'),
  toolButtons: document.querySelectorAll('.btn-tool'),

  // Step 2 Matrix Panel
  tabButtons: document.querySelectorAll('.tab-btn'),
  countAll: document.getElementById('countAll'),
  countUnmapped: document.getElementById('countUnmapped'),
  countMapped: document.getElementById('countMapped'),
  cellSearchInput: document.getElementById('cellSearchInput'),
  cellsListContainer: document.getElementById('cellsListContainer'),
  btnSaveAllMatrix: document.getElementById('btnSaveAllMatrix'),

  // Modals & Drawers
  bulkStopsModal: document.getElementById('bulkStopsModal'),
  bulkStopsTextarea: document.getElementById('bulkStopsTextarea'),
  btnCloseBulkModal: document.getElementById('btnCloseBulkModal'),
  btnCancelBulkModal: document.getElementById('btnCancelBulkModal'),
  btnApplyBulkStops: document.getElementById('btnApplyBulkStops'),
  proofPreviewModal: document.getElementById('proofPreviewModal'),
  proofModalTitle: document.getElementById('proofModalTitle'),
  proofLoadingSpinner: document.getElementById('proofLoadingSpinner'),
  proofPreviewImage: document.getElementById('proofPreviewImage'),
  btnCloseProofModal: document.getElementById('btnCloseProofModal'),
  btnCloseProofModal2: document.getElementById('btnCloseProofModal2'),
  routesDrawer: document.getElementById('routesDrawer'),
  routesCatalogList: document.getElementById('routesCatalogList'),
  btnCloseDrawer: document.getElementById('btnCloseDrawer'),
  toastContainer: document.getElementById('toastContainer')
};

// Canvas Context
let ctx = null;

// Initialization
document.addEventListener('DOMContentLoaded', () => {
  initEventListeners();
  initCanvas();
  checkExistingRoutes();
});

function initEventListeners() {
  // Navigation
  elements.btnNewRoute.addEventListener('click', () => switchView('step1'));
  elements.btnOpenRoutesDrawer.addEventListener('click', openRoutesCatalog);
  elements.btnCloseDrawer.addEventListener('click', () => elements.routesDrawer.classList.add('hidden'));

  // Step 1: File Dropzone
  elements.pdfFileInput.addEventListener('change', handleFileSelected);
  elements.pdfDropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.pdfDropzone.classList.add('dragover');
  });
  elements.pdfDropzone.addEventListener('dragleave', () => elements.pdfDropzone.classList.remove('dragover'));
  elements.pdfDropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.pdfDropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
      elements.pdfFileInput.files = e.dataTransfer.files;
      handleFileSelected();
    }
  });

  // Step 1: Stops
  elements.btnAddStop.addEventListener('click', addStopFromInput);
  elements.newStopInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addStopFromInput();
    }
  });
  elements.btnPasteBulkStops.addEventListener('click', () => elements.bulkStopsModal.classList.remove('hidden'));
  elements.btnCloseBulkModal.addEventListener('click', () => elements.bulkStopsModal.classList.add('hidden'));
  elements.btnCancelBulkModal.addEventListener('click', () => elements.bulkStopsModal.classList.add('hidden'));
  elements.btnApplyBulkStops.addEventListener('click', applyBulkStops);
  elements.btnLoadSampleStops.addEventListener('click', loadSampleStops);

  // Step 1: Submit Form
  elements.routeInitForm.addEventListener('submit', handleRouteInitSubmit);

  // Step 2: Tools & Zoom
  elements.toolButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      elements.toolButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.activeDrawTarget = btn.dataset.target;
      showToast(`Drawing mode set to: ${btn.textContent.trim()}`, 'info');
    });
  });

  elements.btnZoomIn.addEventListener('click', () => setZoom(state.zoom + 0.2));
  elements.btnZoomOut.addEventListener('click', () => setZoom(state.zoom - 0.2));
  elements.btnResetZoom.addEventListener('click', () => setZoom(1.0));

  // Step 2: Matrix Filters
  elements.tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      elements.tabButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.filter = btn.dataset.filter;
      renderCellsList();
    });
  });

  elements.cellSearchInput.addEventListener('input', (e) => {
    state.searchQuery = e.target.value.toLowerCase().trim();
    renderCellsList();
  });

  elements.btnSaveAllMatrix.addEventListener('click', handleSaveAllMatrix);

  // Modals
  elements.btnCloseProofModal.addEventListener('click', () => elements.proofPreviewModal.classList.add('hidden'));
  elements.btnCloseProofModal2.addEventListener('click', () => elements.proofPreviewModal.classList.add('hidden'));
}

// -------------------------------------------------------------
// View Management
// -------------------------------------------------------------
function switchView(viewName) {
  if (viewName === 'step1') {
    elements.step1View.classList.add('active');
    elements.step2View.classList.remove('active');
    elements.routeHeaderStats.classList.add('hidden');
  } else if (viewName === 'step2') {
    elements.step1View.classList.remove('active');
    elements.step2View.classList.add('active');
    elements.routeHeaderStats.classList.remove('hidden');
  }
}

// -------------------------------------------------------------
// Step 1: File & Stops Logic
// -------------------------------------------------------------
function handleFileSelected() {
  if (elements.pdfFileInput.files && elements.pdfFileInput.files[0]) {
    const file = elements.pdfFileInput.files[0];
    elements.uploadFilename.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  }
}

function addStopFromInput() {
  const name = elements.newStopInput.value.trim();
  if (!name) return;
  state.stops.push(name);
  elements.newStopInput.value = '';
  renderStopsList();
  elements.newStopInput.focus();
}

function removeStop(index) {
  state.stops.splice(index, 1);
  renderStopsList();
}

function renderStopsList() {
  if (state.stops.length === 0) {
    elements.stopsListContainer.innerHTML = '<div class="empty-stops-hint">No stops added yet. Add stops one-by-one or paste a list.</div>';
    elements.stopsSummaryBadge.classList.add('hidden');
    return;
  }

  elements.stopsListContainer.innerHTML = state.stops.map((stop, idx) => `
    <div class="stop-pill">
      <span class="stop-num">${idx + 1}</span>
      <span>${escapeHtml(stop)}</span>
      <span class="btn-remove-stop" onclick="removeStop(${idx})">&times;</span>
    </div>
  `).join('');

  const n = state.stops.length;
  const pairs = (n * (n - 1)) / 2;
  elements.stopsCountText.textContent = `${n} stops`;
  elements.pairsCountText.textContent = `${pairs} matrix pairs`;
  elements.stopsSummaryBadge.classList.remove('hidden');
}

function applyBulkStops() {
  const text = elements.bulkStopsTextarea.value.trim();
  if (!text) return;

  const lines = text.split('\n')
    .map(line => line.replace(/^[\d\.\-\)\s]+/, '').trim())
    .filter(line => line.length > 0);

  if (lines.length > 0) {
    state.stops = lines;
    renderStopsList();
    elements.bulkStopsModal.classList.add('hidden');
    showToast(`Loaded ${lines.length} stops.`, 'success');
  }
}

function loadSampleStops() {
  state.stops = [
    "Kalsi",
    "Mirpur-12",
    "Mirpur-10",
    "Kazipara",
    "Shewrapara",
    "Farmgate",
    "Shahbag",
    "Paltan",
    "Gulistan",
    "Tikatuli",
    "Jatrabari",
    "Signboard",
    "Kanchpur Bridge"
  ];
  renderStopsList();
  if (!elements.routeName.value) {
    elements.routeName.value = "Kalsi (Mirpur-12) to Kanchpur Bridge";
  }
  if (!elements.routeNumber.value) {
    elements.routeNumber.value = "A-101";
  }
  if (!elements.ratePerKm.value) {
    elements.ratePerKm.value = "2.50";
  }
  if (!elements.minFare.value) {
    elements.minFare.value = "10.00";
  }
  showToast("Loaded sample 13 stops list!", 'success');
}

async function handleRouteInitSubmit(e) {
  e.preventDefault();

  if (state.stops.length < 2) {
    showToast("Please enter at least 2 stops.", "error");
    return;
  }

  const file = elements.pdfFileInput.files[0];
  if (!file) {
    showToast("Please select a PDF file.", "error");
    return;
  }

  const formData = new FormData();
  formData.append('pdf_file', file);
  formData.append('route_name', elements.routeName.value.trim());
  if (elements.routeNumber.value) formData.append('route_number', elements.routeNumber.value.trim());
  if (elements.ratePerKm.value) formData.append('rate_per_km', elements.ratePerKm.value);
  if (elements.minFare.value) formData.append('min_fare', elements.minFare.value);
  formData.append('stops', JSON.stringify(state.stops));

  try {
    elements.btnSubmitStep1.disabled = true;
    elements.btnSubmitStep1.innerHTML = 'Initializing Matrix & Processing PDF...';

    const res = await fetch(`${API_BASE}/admin/routes/upload-and-init`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create route');
    }

    const routeData = await res.json();
    showToast(`Route created! Generated ${routeData.total_cells} matrix cells.`, 'success');
    loadRouteIntoWorkspace(routeData);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    elements.btnSubmitStep1.disabled = false;
    elements.btnSubmitStep1.innerHTML = 'Generate Fare Matrix & Start Mapping <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>';
  }
}

// -------------------------------------------------------------
// Step 2: Workspace & Canvas Logic
// -------------------------------------------------------------
function loadRouteIntoWorkspace(routeData) {
  state.currentRoute = routeData;
  state.activeCellId = routeData.cells.length > 0 ? routeData.cells[0].cell_id : null;

  // Update Header
  elements.headerRouteTitle.textContent = routeData.route_name;
  updateHeaderProgress();

  // Load Chart Image
  const imageUrl = `${API_BASE}/admin/routes/${routeData.route_id}/page-image?t=${Date.now()}`;
  elements.chartImage.src = imageUrl;

  elements.chartImage.onload = () => {
    state.imageNaturalWidth = elements.chartImage.naturalWidth;
    state.imageNaturalHeight = elements.chartImage.naturalHeight;
    elements.interactiveCanvas.width = state.imageNaturalWidth;
    elements.interactiveCanvas.height = state.imageNaturalHeight;
    redrawCanvas();
    renderCellsList();
    switchView('step2');
  };
}

function updateHeaderProgress() {
  if (!state.currentRoute) return;
  const mapped = state.currentRoute.mapped_cells;
  const total = state.currentRoute.total_cells;
  const pct = total > 0 ? Math.round((mapped / total) * 100) : 0;
  elements.headerProgressBadge.textContent = `${mapped} / ${total} Mapped (${pct}%)`;

  elements.countAll.textContent = total;
  elements.countMapped.textContent = mapped;
  elements.countUnmapped.textContent = total - mapped;
}

function initCanvas() {
  const canvas = elements.interactiveCanvas;
  ctx = canvas.getContext('2d');

  canvas.addEventListener('mousedown', onCanvasMouseDown);
  canvas.addEventListener('mousemove', onCanvasMouseMove);
  canvas.addEventListener('mouseup', onCanvasMouseUp);
}

function setZoom(newZoom) {
  state.zoom = Math.max(0.4, Math.min(3.0, newZoom));
  elements.zoomLevelDisplay.textContent = `${Math.round(state.zoom * 100)}%`;
  elements.canvasWrapper.style.transform = `scale(${state.zoom})`;
}

function getCanvasCoords(event) {
  const rect = elements.interactiveCanvas.getBoundingClientRect();
  const scaleX = elements.interactiveCanvas.width / rect.width;
  const scaleY = elements.interactiveCanvas.height / rect.height;

  const x = Math.round((event.clientX - rect.left) * scaleX);
  const y = Math.round((event.clientY - rect.top) * scaleY);
  return { x: Math.max(0, x), y: Math.max(0, y) };
}

function onCanvasMouseDown(e) {
  if (!state.activeCellId) return;
  const coords = getCanvasCoords(e);
  state.isDrawing = true;
  state.drawStart = coords;
  state.currentRect = { x: coords.x, y: coords.y, width: 0, height: 0 };
}

function onCanvasMouseMove(e) {
  const coords = getCanvasCoords(e);
  elements.coordsTracker.textContent = `X: ${coords.x}, Y: ${coords.y} | Target: ${state.activeDrawTarget}`;

  if (!state.isDrawing) return;

  const x = Math.min(state.drawStart.x, coords.x);
  const y = Math.min(state.drawStart.y, coords.y);
  const width = Math.abs(coords.x - state.drawStart.x);
  const height = Math.abs(coords.y - state.drawStart.y);

  state.currentRect = { x, y, width, height };
  redrawCanvas();
}

async function onCanvasMouseUp(e) {
  if (!state.isDrawing) return;
  state.isDrawing = false;

  if (state.currentRect && state.currentRect.width > 5 && state.currentRect.height > 5) {
    const cell = getActiveCell();
    if (cell) {
      cell[state.activeDrawTarget] = { ...state.currentRect };
      redrawCanvas();
      renderCellsList();
      showToast(`Updated ${state.activeDrawTarget} for cell [${cell.cell_id}]`, 'info');
      await autoSaveActiveCell();
    }
  }
  state.currentRect = null;
}

function getActiveCell() {
  if (!state.currentRoute || !state.activeCellId) return null;
  return state.currentRoute.cells.find(c => c.cell_id === state.activeCellId);
}

function redrawCanvas() {
  if (!ctx || !elements.interactiveCanvas.width) return;
  ctx.clearRect(0, 0, elements.interactiveCanvas.width, elements.interactiveCanvas.height);

  const cell = getActiveCell();
  if (cell) {
    // Draw source stop box (Blue)
    if (cell.source_box) {
      drawBoxOnCanvas(cell.source_box, '#2563eb', 'Source Stop');
    }
    // Draw destination stop box (Cyan)
    if (cell.destination_box) {
      drawBoxOnCanvas(cell.destination_box, '#06b6d4', 'Dest Stop');
    }
    // Draw fare box (Red)
    if (cell.fare_box) {
      drawBoxOnCanvas(cell.fare_box, '#ef4444', `Fare: ${cell.amount ? cell.amount + ' Tk' : 'Cell'}`);
    }
  }

  // Draw current dragging rectangle
  if (state.isDrawing && state.currentRect) {
    const color = state.activeDrawTarget === 'fare_box' ? '#ef4444' : '#2563eb';
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.setLineDash([4, 4]);
    ctx.strokeRect(state.currentRect.x, state.currentRect.y, state.currentRect.width, state.currentRect.height);
    ctx.setLineDash([]);
  }
}

function drawBoxOnCanvas(box, color, label) {
  ctx.strokeStyle = color;
  ctx.lineWidth = 3;
  ctx.strokeRect(box.x, box.y, box.width, box.height);

  ctx.fillStyle = color.replace(')', ', 0.2)').replace('rgb', 'rgba').replace('#2563eb', 'rgba(37,99,235,0.2)').replace('#ef4444', 'rgba(239,68,68,0.25)').replace('#06b6d4', 'rgba(6,182,212,0.2)');
  ctx.fillRect(box.x, box.y, box.width, box.height);

  // Label badge
  ctx.fillStyle = color;
  ctx.fillRect(box.x, box.y - 18, Math.max(60, label.length * 8), 18);
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 11px Inter, sans-serif';
  ctx.fillText(label, box.x + 4, box.y - 4);
}

// -------------------------------------------------------------
// Matrix Cells List Rendering & API Sync
// -------------------------------------------------------------
function renderCellsList() {
  if (!state.currentRoute) return;

  let cells = state.currentRoute.cells;

  // Filter
  if (state.filter === 'unmapped') {
    cells = cells.filter(c => !c.is_mapped);
  } else if (state.filter === 'mapped') {
    cells = cells.filter(c => c.is_mapped);
  }

  // Search
  if (state.searchQuery) {
    cells = cells.filter(c => 
      c.source_name.toLowerCase().includes(state.searchQuery) ||
      c.destination_name.toLowerCase().includes(state.searchQuery) ||
      c.cell_id.includes(state.searchQuery)
    );
  }

  if (cells.length === 0) {
    elements.cellsListContainer.innerHTML = '<div class="empty-stops-hint">No matrix cells match criteria.</div>';
    return;
  }

  elements.cellsListContainer.innerHTML = cells.map(cell => {
    const isActive = cell.cell_id === state.activeCellId;
    const isMapped = cell.is_mapped;

    return `
      <div class="cell-card ${isActive ? 'active' : ''}" data-cell-id="${cell.cell_id}" onclick="selectCell('${cell.cell_id}')">
        <div class="cell-card-header">
          <span class="cell-pair-title">
            <strong>${cell.source_stop_id}. ${escapeHtml(cell.source_name)}</strong> 
            <span class="arrow">$\rightarrow$</span> 
            <strong>${cell.destination_stop_id}. ${escapeHtml(cell.destination_name)}</strong>
          </span>
          <span class="cell-status-dot ${isMapped ? 'mapped' : ''}" title="${isMapped ? 'Mapped' : 'Pending'}"></span>
        </div>

        <div class="cell-inputs-row">
          <div class="cell-input-group">
            <label>Fare Amount (Tk)</label>
            <input type="number" step="0.5" value="${cell.amount !== null && cell.amount !== undefined ? cell.amount : ''}" 
              placeholder="e.g. 20" 
              onchange="updateCellAmount('${cell.cell_id}', this.value)"
              onclick="event.stopPropagation()">
          </div>
          <div class="cell-input-group">
            <label>Distance (Km)</label>
            <input type="number" step="0.1" value="${cell.distance_km !== null && cell.distance_km !== undefined ? cell.distance_km : ''}" 
              placeholder="e.g. 5.4" 
              onchange="updateCellDistance('${cell.cell_id}', this.value)"
              onclick="event.stopPropagation()">
          </div>
        </div>

        <div class="cell-boxes-status">
          <span class="box-tag ${cell.source_box ? 'set' : ''}">Src: ${cell.source_box ? '✓' : 'None'}</span>
          <span class="box-tag ${cell.destination_box ? 'set' : ''}">Dest: ${cell.destination_box ? '✓' : 'None'}</span>
          <span class="box-tag fare ${cell.fare_box ? 'set' : ''}">Fare Box: ${cell.fare_box ? '✓' : 'None'}</span>
        </div>

        <div class="cell-card-actions">
          <span class="cell-auto-save-note">${isMapped ? '✓ Ready' : 'Draw boxes on canvas'}</span>
          <button type="button" class="btn btn-sm btn-secondary" onclick="event.stopPropagation(); previewProof('${cell.cell_id}')">
            👁️ Preview
          </button>
        </div>
      </div>
    `;
  }).join('');
}

window.selectCell = function(cellId) {
  state.activeCellId = cellId;
  const cell = getActiveCell();
  if (cell) {
    elements.activeCellInfo.textContent = `Active Cell: [${cell.cell_id}] ${cell.source_name} → ${cell.destination_name}`;
  }
  redrawCanvas();
  renderCellsList();
};

window.updateCellAmount = async function(cellId, value) {
  const cell = state.currentRoute.cells.find(c => c.cell_id === cellId);
  if (cell) {
    cell.amount = value !== '' ? parseFloat(value) : null;
    cell.is_mapped = (cell.amount !== null && cell.fare_box !== null);
    updateHeaderProgress();
    await autoSaveActiveCell(cellId);
  }
};

window.updateCellDistance = async function(cellId, value) {
  const cell = state.currentRoute.cells.find(c => c.cell_id === cellId);
  if (cell) {
    cell.distance_km = value !== '' ? parseFloat(value) : null;
    await autoSaveActiveCell(cellId);
  }
};

async function autoSaveActiveCell(targetCellId = null) {
  const cid = targetCellId || state.activeCellId;
  if (!state.currentRoute || !cid) return;

  const cell = state.currentRoute.cells.find(c => c.cell_id === cid);
  if (!cell) return;

  const payload = {
    amount: cell.amount,
    distance_km: cell.distance_km,
    source_box: cell.source_box,
    destination_box: cell.destination_box,
    fare_box: cell.fare_box
  };

  try {
    const res = await fetch(`${API_BASE}/admin/routes/${state.currentRoute.route_id}/cells/${cid}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const updatedRoute = await res.json();
      state.currentRoute.mapped_cells = updatedRoute.mapped_cells;
      updateHeaderProgress();
    }
  } catch (err) {
    console.error("Auto-save error:", err);
  }
}

async function handleSaveAllMatrix() {
  if (!state.currentRoute) return;

  try {
    elements.btnSaveAllMatrix.disabled = true;
    elements.btnSaveAllMatrix.innerHTML = 'Saving Entire Matrix...';

    const res = await fetch(`${API_BASE}/admin/routes/${state.currentRoute.route_id}/matrix`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cells: state.currentRoute.cells })
    });

    if (!res.ok) throw new Error("Failed to save matrix");

    const updated = await res.json();
    state.currentRoute = updated;
    updateHeaderProgress();
    renderCellsList();
    showToast("All matrix changes saved successfully!", 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    elements.btnSaveAllMatrix.disabled = false;
    elements.btnSaveAllMatrix.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg> Save All Matrix Changes';
  }
}

// -------------------------------------------------------------
// Visual Proof Preview Modal
// -------------------------------------------------------------
window.previewProof = function(cellId) {
  const cell = state.currentRoute.cells.find(c => c.cell_id === cellId);
  if (!cell) return;

  elements.proofModalTitle.textContent = `Proof Highlight: ${cell.source_name} → ${cell.destination_name} (${cell.amount || '0'} Tk)`;
  elements.proofPreviewModal.classList.remove('hidden');
  elements.proofLoadingSpinner.classList.remove('hidden');
  elements.proofPreviewImage.classList.add('hidden');

  const previewUrl = `${API_BASE}/admin/routes/${state.currentRoute.route_id}/preview-cell/${cellId}?t=${Date.now()}`;
  elements.proofPreviewImage.src = previewUrl;

  elements.proofPreviewImage.onload = () => {
    elements.proofLoadingSpinner.classList.add('hidden');
    elements.proofPreviewImage.classList.remove('hidden');
  };
};

// -------------------------------------------------------------
// Routes Catalog Drawer
// -------------------------------------------------------------
async function openRoutesCatalog() {
  elements.routesDrawer.classList.remove('hidden');
  elements.routesCatalogList.innerHTML = '<div class="loading-text">Loading routes...</div>';

  try {
    const res = await fetch(`${API_BASE}/admin/routes`);
    const routes = await res.json();

    if (routes.length === 0) {
      elements.routesCatalogList.innerHTML = '<div class="empty-stops-hint">No saved routes found. Create a new route.</div>';
      return;
    }

    elements.routesCatalogList.innerHTML = routes.map(r => `
      <div class="catalog-item" onclick="loadSavedRoute('${r.route_id}')">
        <div class="catalog-item-title">${escapeHtml(r.route_name)}</div>
        <div class="catalog-item-meta">
          <span>Stops: ${r.total_stops}</span>
          <span class="badge ${r.mapped_cells === r.total_cells ? 'badge-success' : 'badge-warning'}">
            ${r.mapped_cells} / ${r.total_cells} Mapped
          </span>
        </div>
      </div>
    `).join('');
  } catch (err) {
    elements.routesCatalogList.innerHTML = `<div class="text-danger">Error loading routes: ${err.message}</div>`;
  }
}

window.loadSavedRoute = async function(routeId) {
  try {
    const res = await fetch(`${API_BASE}/admin/routes/${routeId}`);
    if (!res.ok) throw new Error("Route not found");
    const data = await res.json();
    elements.routesDrawer.classList.add('hidden');
    loadRouteIntoWorkspace(data);
    showToast(`Loaded route: ${data.route_name}`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
};

async function checkExistingRoutes() {
  try {
    const res = await fetch(`${API_BASE}/admin/routes`);
    const routes = await res.json();
    if (routes.length > 0) {
      // Auto-load most recent route if available
      loadSavedRoute(routes[0].route_id);
    }
  } catch (e) {
    // API not ready yet or empty
  }
}

// -------------------------------------------------------------
// Fare Search Tester Modal Logic
// -------------------------------------------------------------
const btnOpenSearchModal = document.getElementById('btnOpenSearchModal');
const fareSearchModal = document.getElementById('fareSearchModal');
const btnCloseSearchModal = document.getElementById('btnCloseSearchModal');
const fareSearchForm = document.getElementById('fareSearchForm');
const searchSource = document.getElementById('searchSource');
const searchDest = document.getElementById('searchDest');
const searchResultsCard = document.getElementById('searchResultsCard');
const resPairTitle = document.getElementById('resPairTitle');
const resFareAmount = document.getElementById('resFareAmount');
const resDistance = document.getElementById('resDistance');
const btnViewSearchResultProof = document.getElementById('btnViewSearchResultProof');
let currentSearchChartUrl = null;

if (btnOpenSearchModal) {
  btnOpenSearchModal.addEventListener('click', () => {
    fareSearchModal.classList.remove('hidden');
    searchSource.focus();
  });
}

if (btnCloseSearchModal) {
  btnCloseSearchModal.addEventListener('click', () => {
    fareSearchModal.classList.add('hidden');
  });
}

if (fareSearchForm) {
  fareSearchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const src = searchSource.value.trim();
    const dest = searchDest.value.trim();
    if (!src || !dest) return;

    try {
      searchResultsCard.classList.add('hidden');
      const res = await fetch(`${API_BASE}/fares/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: src, destination: dest })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Fare not found');
      }

      const data = await res.json();
      resPairTitle.textContent = `${data.source} → ${data.destination}`;
      resFareAmount.textContent = `${data.calculated_fare} Tk`;
      resDistance.textContent = `Distance: ${data.distance_km} km`;
      currentSearchChartUrl = data.chart_url;
      searchResultsCard.classList.remove('hidden');
      showToast("Found matching fare!", "success");
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

if (btnViewSearchResultProof) {
  btnViewSearchResultProof.addEventListener('click', () => {
    if (!currentSearchChartUrl) return;
    elements.proofModalTitle.textContent = `Government Chart Proof: ${resPairTitle.textContent} (${resFareAmount.textContent})`;
    elements.proofPreviewModal.classList.remove('hidden');
    elements.proofLoadingSpinner.classList.remove('hidden');
    elements.proofPreviewImage.classList.add('hidden');
    elements.proofPreviewImage.src = currentSearchChartUrl + `?t=${Date.now()}`;
    elements.proofPreviewImage.onload = () => {
      elements.proofLoadingSpinner.classList.add('hidden');
      elements.proofPreviewImage.classList.remove('hidden');
    };
  });
}

// -------------------------------------------------------------
// Toast Notification Utility
// -------------------------------------------------------------
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  elements.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 200);
  }, 3000);
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

