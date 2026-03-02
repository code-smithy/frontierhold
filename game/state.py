from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GameState:
    tick: int = 0

    def to_dict(self) -> dict[str, int]:
        return {"tick": self.tick}
