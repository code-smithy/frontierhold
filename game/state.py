from __future__ import annotations

from dataclasses import dataclass, field
import random

GRID_SIZE = 25
TERRAINS = ("plains", "forest", "hill", "water")
ROLES = ("idle", "lumberjack", "farmer", "miner", "builder", "militia")

BUILDING_CONFIG = {
    "farm": {
        "cost": {"wood": 20, "stone": 5},
        "build_time": 24,
        "allowed_terrain": {"plains"},
        "supports_farmers": 3,
    },
    "house": {
        "cost": {"wood": 30, "stone": 10},
        "build_time": 36,
        "allowed_terrain": {"plains", "forest"},
        "housing_bonus": 5,
    },
}

PRODUCTION = {
    "lumberjack": {"wood": 2},
    "farmer": {"food": 3},
    "miner": {"ore": 1, "stone": 1},
}

FOOD_PER_PERSON_TENTHS = 1  # 0.1 food / hour


def generate_map(size: int = GRID_SIZE, seed: int = 42) -> list[list[str]]:
    rng = random.Random(seed)
    terrain_weights = [0.5, 0.25, 0.15, 0.1]
    return [
        [rng.choices(TERRAINS, weights=terrain_weights, k=1)[0] for _ in range(size)]
        for _ in range(size)
    ]


@dataclass
class Building:
    type: str
    x: int
    y: int
    construction_progress: int = 0
    construction_required: int = 0
    status: str = "queued"

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "construction_progress": self.construction_progress,
            "construction_required": self.construction_required,
            "status": self.status,
        }


@dataclass
class GameState:
    tick: int = 0
    map_size: int = GRID_SIZE
    terrain_map: list[list[str]] = field(default_factory=generate_map)
    population_alive: int = 20
    housing_capacity_base: int = 0
    resources: dict[str, int] = field(
        default_factory=lambda: {"food_tenths": 1000, "wood": 100, "stone": 100, "ore": 100}
    )
    workers: dict[str, int] = field(
        default_factory=lambda: {
            "idle": 20,
            "lumberjack": 0,
            "farmer": 0,
            "miner": 0,
            "builder": 0,
            "militia": 0,
        }
    )
    buildings: list[Building] = field(default_factory=list)
    construction_queue: list[Building] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._create_starting_houses(2)

    def _create_starting_houses(self, count: int) -> None:
        placed = 0
        for y in range(self.map_size):
            for x in range(self.map_size):
                if self.terrain_map[y][x] in BUILDING_CONFIG["house"]["allowed_terrain"] and not self.building_at(x, y):
                    self.buildings.append(
                        Building(
                            type="house",
                            x=x,
                            y=y,
                            construction_progress=BUILDING_CONFIG["house"]["build_time"],
                            construction_required=BUILDING_CONFIG["house"]["build_time"],
                            status="completed",
                        )
                    )
                    placed += 1
                    if placed >= count:
                        return

    @property
    def housing_capacity(self) -> int:
        completed_houses = sum(1 for b in self.buildings if b.type == "house" and b.status == "completed")
        return self.housing_capacity_base + completed_houses * BUILDING_CONFIG["house"]["housing_bonus"]

    def completed_buildings_of_type(self, building_type: str) -> int:
        return sum(1 for b in self.buildings if b.type == building_type and b.status == "completed")

    def building_at(self, x: int, y: int) -> Building | None:
        for building in self.buildings:
            if building.x == x and building.y == y:
                return building
        return None

    def to_dict(self) -> dict:
        return {
            "tick": self.tick,
            "map_size": self.map_size,
            "terrain_map": self.terrain_map,
            "population_alive": self.population_alive,
            "housing_capacity": self.housing_capacity,
            "resources": {
                "food": round(self.resources["food_tenths"] / 10, 1),
                "wood": self.resources["wood"],
                "stone": self.resources["stone"],
                "ore": self.resources["ore"],
            },
            "workers": self.workers,
            "buildings": [building.to_dict() for building in self.buildings],
            "construction_queue": [building.to_dict() for building in self.construction_queue],
            "projections": {
                "food_delta": round(self.hourly_resource_deltas()["food_tenths"] / 10, 1),
                "wood_delta": self.hourly_resource_deltas()["wood"],
                "stone_delta": self.hourly_resource_deltas()["stone"],
                "ore_delta": self.hourly_resource_deltas()["ore"],
            },
            "warnings": {
                "starvation_next_tick": self.resources["food_tenths"] + self.hourly_resource_deltas()["food_tenths"] < 0,
                "no_builders": self.workers["builder"] == 0,
                "idle_workers": self.workers["idle"],
                "overpopulated": self.population_alive > self.housing_capacity,
            },
            "wheat_fields": self.wheat_fields(),
        }

    def hourly_resource_deltas(self) -> dict[str, int]:
        deltas = {"food_tenths": 0, "wood": 0, "stone": 0, "ore": 0}

        deltas["wood"] += self.workers["lumberjack"] * PRODUCTION["lumberjack"]["wood"]
        deltas["stone"] += self.workers["miner"] * PRODUCTION["miner"]["stone"]
        deltas["ore"] += self.workers["miner"] * PRODUCTION["miner"]["ore"]

        farms = self.completed_buildings_of_type("farm")
        active_farmers = min(self.workers["farmer"], farms * BUILDING_CONFIG["farm"]["supports_farmers"])
        deltas["food_tenths"] += active_farmers * PRODUCTION["farmer"]["food"] * 10

        deltas["food_tenths"] -= self.population_alive * FOOD_PER_PERSON_TENTHS
        return deltas

    def wheat_fields(self) -> list[dict[str, int]]:
        fields: list[dict[str, int]] = []
        remaining = min(
            self.workers["farmer"],
            self.completed_buildings_of_type("farm") * BUILDING_CONFIG["farm"]["supports_farmers"],
        )
        for farm in [b for b in self.buildings if b.type == "farm" and b.status == "completed"]:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    x = farm.x + dx
                    y = farm.y + dy
                    if 0 <= x < self.map_size and 0 <= y < self.map_size and self.terrain_map[y][x] == "plains":
                        fields.append({"x": x, "y": y})
                        remaining -= 1
                        if remaining <= 0:
                            return fields
        return fields
