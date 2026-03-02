from __future__ import annotations

from math import ceil

from game.state import BUILDING_CONFIG, GameState


def assign_workers(state: GameState, assignments: dict[str, int]) -> None:
    required_roles = {"lumberjack", "farmer", "miner", "builder", "militia"}
    if set(assignments) != required_roles:
        raise ValueError("Assignments must include lumberjack, farmer, miner, builder, and militia")

    if any(value < 0 for value in assignments.values()):
        raise ValueError("Worker assignments cannot be negative")

    assigned_total = sum(assignments.values())
    if assigned_total > state.population_alive:
        raise ValueError("Assigned workers exceed alive population")

    state.workers.update(assignments)
    state.workers["idle"] = state.population_alive - assigned_total


def queue_building(state: GameState, building_type: str, x: int, y: int) -> None:
    if building_type not in BUILDING_CONFIG:
        raise ValueError("Unknown building type")
    if not (0 <= x < state.map_size and 0 <= y < state.map_size):
        raise ValueError("Coordinates out of bounds")
    if state.building_at(x, y) is not None:
        raise ValueError("Tile already occupied")

    terrain = state.terrain_map[y][x]
    allowed_terrain = BUILDING_CONFIG[building_type]["allowed_terrain"]
    if terrain not in allowed_terrain:
        raise ValueError(f"{building_type} cannot be built on {terrain}")

    cost = BUILDING_CONFIG[building_type]["cost"]
    for resource_name, amount in cost.items():
        if state.resources[resource_name] < amount:
            raise ValueError(f"Insufficient {resource_name}")

    for resource_name, amount in cost.items():
        state.resources[resource_name] -= amount

    from game.state import Building

    building = Building(
        type=building_type,
        x=x,
        y=y,
        construction_progress=0,
        construction_required=BUILDING_CONFIG[building_type]["build_time"],
        status="queued",
    )
    state.buildings.append(building)
    state.construction_queue.append(building)


def _auto_rebalance_workers(state: GameState) -> None:
    overflow = max(0, sum(state.workers.values()) - state.population_alive)
    for role in ["idle", "builder", "lumberjack", "farmer", "miner", "militia"]:
        if overflow <= 0:
            break
        reducible = min(state.workers.get(role, 0), overflow)
        state.workers[role] -= reducible
        overflow -= reducible

    assigned_non_idle = sum(state.workers[r] for r in ["lumberjack", "farmer", "miner", "builder", "militia"])
    state.workers["idle"] = max(0, state.population_alive - assigned_non_idle)


def tick(state: GameState) -> GameState:
    state.tick += 1

    deltas = state.hourly_resource_deltas()
    state.resources["wood"] += deltas["wood"]
    state.resources["stone"] += deltas["stone"]
    state.resources["ore"] += deltas["ore"]
    state.resources["food_tenths"] += deltas["food_tenths"]

    if state.construction_queue:
        active = state.construction_queue[0]
        active.status = "building"
        active.construction_progress += state.workers["builder"]
        if active.construction_progress >= active.construction_required:
            active.construction_progress = active.construction_required
            active.status = "completed"
            state.construction_queue.pop(0)

    if state.resources["food_tenths"] < 0:
        deficit_food = ceil(abs(state.resources["food_tenths"]) / 10)
        deaths = min(state.population_alive, ceil(deficit_food / 5))
        state.population_alive -= deaths
        state.resources["food_tenths"] = 0
        _auto_rebalance_workers(state)

    for key in ["food_tenths", "wood", "stone", "ore"]:
        state.resources[key] = max(0, state.resources[key])

    return state
