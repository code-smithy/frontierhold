const tickEl = document.getElementById('tick');
const canvas = document.getElementById('map-canvas');
const ctx = canvas.getContext('2d');

const TERRAIN_COLORS = {
  plains: '#8fae5e',
  forest: '#2e6b3a',
  hill: '#7a6a59'
};

function drawMap(state) {
  const terrainMap = state.terrain_map ?? [];
  const mapSize = state.map_size ?? 25;
  const tile = Math.floor(canvas.width / mapSize);

  ctx.fillStyle = '#0a111d';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  for (let y = 0; y < mapSize; y += 1) {
    for (let x = 0; x < mapSize; x += 1) {
      const terrain = terrainMap[y]?.[x] ?? 'plains';
      ctx.fillStyle = TERRAIN_COLORS[terrain] ?? TERRAIN_COLORS.plains;
      ctx.fillRect(x * tile, y * tile, tile, tile);
    }
  }

  ctx.strokeStyle = 'rgba(8, 13, 22, 0.45)';
  for (let i = 0; i <= mapSize; i += 1) {
    const p = i * tile;
    ctx.beginPath();
    ctx.moveTo(p, 0);
    ctx.lineTo(p, mapSize * tile);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(0, p);
    ctx.lineTo(mapSize * tile, p);
    ctx.stroke();
  }
}

async function refreshState() {
  const res = await fetch('/state');
  const state = await res.json();
  tickEl.textContent = String(state.tick ?? 0);
  drawMap(state);
}

refreshState();
setInterval(refreshState, 1000);
