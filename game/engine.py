from game.state import GameState


def tick(state: GameState) -> GameState:
    state.tick += 1
    return state
