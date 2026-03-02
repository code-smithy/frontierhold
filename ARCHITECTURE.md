# Architecture Principles

- `GameState` is the authoritative source of simulation state.
- `engine.tick(state)` should remain deterministic and side-effect free once full simulation logic is added.
- API routes orchestrate input/output only and should not embed simulation rules.
- Background tick loop advances the global state on a fixed interval.
