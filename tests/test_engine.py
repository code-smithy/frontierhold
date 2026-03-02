from __future__ import annotations

import unittest

from game import engine
from game.state import BUILDING_CONFIG, Building, GameState


class EngineTests(unittest.TestCase):
    def test_assign_workers_updates_idle(self) -> None:
        state = GameState()
        engine.assign_workers(
            state,
            {"lumberjack": 3, "farmer": 4, "miner": 2, "builder": 1, "militia": 0},
        )

        self.assertEqual(state.workers["lumberjack"], 3)
        self.assertEqual(state.workers["farmer"], 4)
        self.assertEqual(state.workers["idle"], 10)

    def test_assign_workers_rejects_over_assignment(self) -> None:
        state = GameState()
        with self.assertRaisesRegex(ValueError, "exceed"):
            engine.assign_workers(
                state,
                {"lumberjack": 10, "farmer": 10, "miner": 5, "builder": 0, "militia": 0},
            )

    def test_queue_building_deducts_resources_and_adds_queue(self) -> None:
        state = GameState()
        x, y = self._find_valid_tile(state, "farm")
        wood_before = state.resources["wood"]
        stone_before = state.resources["stone"]

        engine.queue_building(state, "farm", x, y)

        self.assertEqual(state.resources["wood"], wood_before - BUILDING_CONFIG["farm"]["cost"]["wood"])
        self.assertEqual(state.resources["stone"], stone_before - BUILDING_CONFIG["farm"]["cost"]["stone"])
        self.assertEqual(len(state.construction_queue), 1)
        self.assertEqual(state.construction_queue[0].type, "farm")
        self.assertEqual(state.construction_queue[0].status, "queued")

    def test_tick_advances_single_active_building(self) -> None:
        state = GameState()
        # ensure build can complete in one tick
        building = Building(type="farm", x=5, y=5, construction_progress=0, construction_required=1, status="queued")
        state.buildings.append(building)
        state.construction_queue.append(building)
        state.workers.update({"builder": 1, "idle": 19})

        engine.tick(state)

        self.assertEqual(state.tick, 1)
        self.assertEqual(building.status, "completed")
        self.assertEqual(len(state.construction_queue), 0)

    def test_tick_starvation_causes_soft_deterministic_death(self) -> None:
        state = GameState()
        state.population_alive = 20
        state.resources["food_tenths"] = 0
        state.workers.update({"idle": 20, "lumberjack": 0, "farmer": 0, "miner": 0, "builder": 0, "militia": 0})

        engine.tick(state)

        # deficit is 2 food (20 tenths) -> ceil(2/5)=1 death
        self.assertEqual(state.population_alive, 19)
        self.assertEqual(state.resources["food_tenths"], 0)
        self.assertEqual(sum(state.workers.values()), state.population_alive)

    def test_farm_support_cap_applies_to_food_production(self) -> None:
        state = GameState()
        # one completed farm supports 3 farmers
        state.buildings.append(
            Building(
                type="farm",
                x=6,
                y=6,
                construction_progress=BUILDING_CONFIG["farm"]["build_time"],
                construction_required=BUILDING_CONFIG["farm"]["build_time"],
                status="completed",
            )
        )
        state.workers.update({"farmer": 5, "idle": 15})

        deltas = state.hourly_resource_deltas()

        # active farmers = 3 => +90 tenths food, -20 tenths consumption = +70
        self.assertEqual(deltas["food_tenths"], 70)

    def _find_valid_tile(self, state: GameState, building_type: str) -> tuple[int, int]:
        allowed = BUILDING_CONFIG[building_type]["allowed_terrain"]
        for y in range(state.map_size):
            for x in range(state.map_size):
                if state.terrain_map[y][x] in allowed and state.building_at(x, y) is None:
                    return x, y
        self.fail(f"No valid tile found for {building_type}")


if __name__ == "__main__":
    unittest.main()
