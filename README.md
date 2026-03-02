# Frontier Hold

Frontier Hold is a medieval-flavored idle colony simulator prototype.

## Current scope

- **World size:** `25x25` grid.
- **Tick rate:** `1 second real time = 1 in-game hour`.
- **Population model:** aggregate worker counts with permadeath.
- **Single-player:** one global in-memory simulation instance.

## Implemented gameplay (Phase 1)

- Worker assignment pools: idle, lumberjack, farmer, miner, builder, militia.
- Hourly production and consumption with deterministic starvation deaths.
- Terrain-constrained building placement for Farm and House.
- FIFO construction queue with builder-based progress (`1 builder = 1 progress/hour`).
- Farm support cap (`1 farm supports 3 farmers`) and wheat field rendering for active farmers.

## API

- `GET /state`: returns current game state.
- `POST /assign_workers`
  - Payload: `{ "lumberjack": int, "farmer": int, "miner": int, "builder": int, "militia": int }`
- `POST /build`
  - Payload: `{ "type": "farm|house", "x": int, "y": int }`

## Run locally

```bash
python main.py
```

Open `http://127.0.0.1:8000`.
