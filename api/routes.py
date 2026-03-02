from game.state import GameState


def get_state(state: GameState) -> dict:
    return state.to_dict()
