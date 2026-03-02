const roles = ['lumberjack', 'farmer', 'miner', 'builder', 'militia'];
const terrainColors = { plains: '#8fae5e', forest: '#2e6b3a', hill: '#7a6a59', water: '#315f8f' };

const tickEl = document.getElementById('tick');
const canvas = document.getElementById('map-canvas');
const ctx = canvas.getContext('2d');
const workerForm = document.getElementById('worker-form');
const idleCount = document.getElementById('idle-count');
const warningText = document.getElementById('warning-text');
const queueList = document.getElementById('queue-list');
const eventLog = document.getElementById('event-log');
const buildModeBtn = document.getElementById('build-mode');
const buildTypeSelect = document.getElementById('build-type');

let currentState = null;
let buildMode = false;
let selectedBuildType = buildTypeSelect.value;

function logEvent(message) {
  const li = document.createElement('li');
  li.textContent = `[t${currentState?.tick ?? 0}] ${message}`;
  eventLog.prepend(li);
  while (eventLog.children.length > 10) eventLog.removeChild(eventLog.lastChild);
}

function initWorkerSliders() {
  workerForm.innerHTML = '';
  roles.forEach((role) => {
    const row = document.createElement('div');
    row.className = 'worker-row';
    row.innerHTML = `<label>${role}<span id="${role}-value">0</span></label><input id="${role}" type="range" min="0" max="20" value="0" />`;
    workerForm.appendChild(row);
  });
}

function getAssignments() {
  const data = {};
  roles.forEach((role) => {
    data[role] = Number(document.getElementById(role).value);
  });
  return data;
}

function syncSlidersFromState(state) {
  const max = state.population_alive;
  roles.forEach((role) => {
    const input = document.getElementById(role);
    input.max = String(max);
    input.value = String(state.workers[role] ?? 0);
    document.getElementById(`${role}-value`).textContent = input.value;
  });
  idleCount.textContent = String(state.workers.idle ?? 0);
}

function drawMap(state) {
  const mapSize = state.map_size;
  const tile = Math.floor(canvas.width / mapSize);
  ctx.fillStyle = '#0a111d';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  for (let y = 0; y < mapSize; y += 1) {
    for (let x = 0; x < mapSize; x += 1) {
      const terrain = state.terrain_map[y][x];
      ctx.fillStyle = terrainColors[terrain] ?? terrainColors.plains;
      ctx.fillRect(x * tile, y * tile, tile, tile);
    }
  }

  state.wheat_fields.forEach((field) => {
    ctx.fillStyle = '#f3d76b';
    ctx.fillRect(field.x * tile + tile * 0.25, field.y * tile + tile * 0.25, tile * 0.5, tile * 0.5);
  });

  state.buildings.forEach((b) => {
    ctx.fillStyle = b.type === 'farm' ? '#d4b14a' : '#ced6e6';
    if (b.status !== 'completed') ctx.globalAlpha = 0.55;
    ctx.fillRect(b.x * tile + 1, b.y * tile + 1, tile - 2, tile - 2);
    ctx.globalAlpha = 1;
  });

  if (buildMode) {
    for (let y = 0; y < mapSize; y += 1) {
      for (let x = 0; x < mapSize; x += 1) {
        const hasBuilding = state.buildings.some((b) => b.x === x && b.y === y);
        const terrain = state.terrain_map[y][x];
        const validTerrains = selectedBuildType === 'farm' ? ['plains'] : ['plains', 'forest'];
        const valid = !hasBuilding && validTerrains.includes(terrain);
        ctx.fillStyle = valid ? 'rgba(90, 200, 120, 0.15)' : 'rgba(220, 90, 90, 0.10)';
        ctx.fillRect(x * tile, y * tile, tile, tile);
      }
    }
  }

  ctx.strokeStyle = 'rgba(8, 13, 22, 0.45)';
  for (let i = 0; i <= mapSize; i += 1) {
    const p = i * tile;
    ctx.beginPath(); ctx.moveTo(p, 0); ctx.lineTo(p, mapSize * tile); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, p); ctx.lineTo(mapSize * tile, p); ctx.stroke();
  }
}

async function postJson(path, payload) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

function updatePanels(state) {
  document.getElementById('population').textContent = state.population_alive;
  document.getElementById('housing').textContent = state.housing_capacity;
  document.getElementById('food').textContent = state.resources.food.toFixed(1);
  document.getElementById('wood').textContent = state.resources.wood;
  document.getElementById('stone').textContent = state.resources.stone;
  document.getElementById('ore').textContent = state.resources.ore;
  document.getElementById('food-delta').textContent = state.projections.food_delta.toFixed(1);
  document.getElementById('build-speed').textContent = `${state.workers.builder} progress/h`;
  warningText.textContent = state.warnings.starvation_next_tick ? '⚠️ Starvation likely next tick' : '';
  queueList.innerHTML = state.construction_queue.length
    ? state.construction_queue.map((q) => `<li>${q.type} ${q.construction_progress}/${q.construction_required}</li>`).join('')
    : '<li>No queued construction</li>';
}

async function refreshState() {
  const res = await fetch('/state');
  const state = await res.json();
  currentState = state;
  tickEl.textContent = String(state.tick ?? 0);
  syncSlidersFromState(state);
  updatePanels(state);
  drawMap(state);
}

workerForm.addEventListener('input', () => {
  const assignments = getAssignments();
  roles.forEach((role) => { document.getElementById(`${role}-value`).textContent = String(assignments[role]); });
  const assigned = roles.reduce((sum, role) => sum + assignments[role], 0);
  const idle = Math.max(0, (currentState?.population_alive ?? 0) - assigned);
  idleCount.textContent = String(idle);
});

document.getElementById('apply-workers').addEventListener('click', async () => {
  try {
    const updated = await postJson('/assign_workers', getAssignments());
    currentState = updated;
    logEvent('Workers reassigned');
    syncSlidersFromState(updated);
    updatePanels(updated);
    drawMap(updated);
  } catch (error) {
    warningText.textContent = error.message;
  }
});

buildModeBtn.addEventListener('click', () => {
  buildMode = !buildMode;
  buildModeBtn.textContent = buildMode ? 'Disable Build Mode' : 'Enable Build Mode';
  drawMap(currentState);
});

buildTypeSelect.addEventListener('change', () => {
  selectedBuildType = buildTypeSelect.value;
  drawMap(currentState);
});

canvas.addEventListener('click', async (event) => {
  if (!buildMode || !currentState) return;
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const x = Math.floor((event.clientX - rect.left) * scaleX / (canvas.width / currentState.map_size));
  const y = Math.floor((event.clientY - rect.top) * scaleY / (canvas.height / currentState.map_size));

  try {
    const updated = await postJson('/build', { type: selectedBuildType, x, y });
    currentState = updated;
    logEvent(`Queued ${selectedBuildType} at (${x}, ${y})`);
    updatePanels(updated);
    drawMap(updated);
  } catch (error) {
    warningText.textContent = error.message;
  }
});

initWorkerSliders();
refreshState();
setInterval(refreshState, 1000);
