# Frontier Hold

Frontier Hold is a medieval-flavored idle colony simulator prototype.

## V1 Contract

- **World size:** `25x25` grid.
- **Tick rate:** `1 second real time = 1 in-game hour`.
- **Population model:** aggregate worker counts (no per-villager objects).
- **Single-player:** one global in-memory simulation instance.

### Planned simulation systems

- Resources: wood, stone, food.
- Worker assignments: lumberjacks, farmers, miners, builders, militia, idle.
- Buildings with construction progress and terrain constraints.
- Danger growth and raid events with permanent casualties.

### API (initial scaffold)

- `GET /state`: returns current game state.

This repository currently includes a minimal FastAPI scaffold with a background tick loop and static frontend shell.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`.
