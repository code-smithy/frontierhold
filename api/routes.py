from __future__ import annotations

from game import engine
from game.state import GameState


def get_state(state: GameState) -> dict:
    return state.to_dict()


def assign_workers(state: GameState, payload: dict) -> dict:
    assignments = {
        "lumberjack": int(payload.get("lumberjack", 0)),
        "farmer": int(payload.get("farmer", 0)),
        "miner": int(payload.get("miner", 0)),
        "builder": int(payload.get("builder", 0)),
        "militia": int(payload.get("militia", 0)),
    }
    engine.assign_workers(state, assignments)
    return state.to_dict()


def build(state: GameState, payload: dict) -> dict:
    building_type = str(payload.get("type", "")).lower()
    x = int(payload.get("x", -1))
    y = int(payload.get("y", -1))
    engine.queue_building(state, building_type, x, y)
    return state.to_dict()
