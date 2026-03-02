const tickEl = document.getElementById('tick');

async function refreshState() {
  const res = await fetch('/state');
  const state = await res.json();
  tickEl.textContent = String(state.tick ?? 0);
}

refreshState();
setInterval(refreshState, 1000);
