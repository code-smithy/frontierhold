from __future__ import annotations

from dataclasses import dataclass, field
import random

GRID_SIZE = 25
TERRAINS = ("plains", "forest", "hill")


def generate_map(size: int = GRID_SIZE, seed: int = 42) -> list[list[str]]:
    rng = random.Random(seed)
    terrain_weights = [0.55, 0.3, 0.15]
    return [
        [rng.choices(TERRAINS, weights=terrain_weights, k=1)[0] for _ in range(size)]
        for _ in range(size)
    ]


@dataclass
class GameState:
    tick: int = 0
    map_size: int = GRID_SIZE
    terrain_map: list[list[str]] = field(default_factory=generate_map)

    def to_dict(self) -> dict:
        return {
            "tick": self.tick,
            "map_size": self.map_size,
            "terrain_map": self.terrain_map,
        }
