from __future__ import annotations

import unittest

from api import routes
from game.state import BUILDING_CONFIG, GameState


class RoutesTests(unittest.TestCase):
    def test_assign_workers_route_returns_updated_state(self) -> None:
        state = GameState()

        payload = {"lumberjack": 2, "farmer": 3, "miner": 1, "builder": 0, "militia": 1}
        result = routes.assign_workers(state, payload)

        self.assertEqual(result["workers"]["lumberjack"], 2)
        self.assertEqual(result["workers"]["idle"], 13)

    def test_build_route_rejects_invalid_terrain(self) -> None:
        state = GameState()
        # find a non-plains tile for farm placement
        target = None
        for y in range(state.map_size):
            for x in range(state.map_size):
                if state.terrain_map[y][x] != "plains" and state.building_at(x, y) is None:
                    target = (x, y)
                    break
            if target:
                break
        self.assertIsNotNone(target)

        with self.assertRaises(ValueError):
            routes.build(state, {"type": "farm", "x": target[0], "y": target[1]})

    def test_build_route_success(self) -> None:
        state = GameState()
        target = None
        for y in range(state.map_size):
            for x in range(state.map_size):
                if state.terrain_map[y][x] in BUILDING_CONFIG["house"]["allowed_terrain"] and state.building_at(x, y) is None:
                    target = (x, y)
                    break
            if target:
                break
        self.assertIsNotNone(target)

        result = routes.build(state, {"type": "house", "x": target[0], "y": target[1]})
        self.assertEqual(result["construction_queue"][0]["type"], "house")


if __name__ == "__main__":
    unittest.main()
