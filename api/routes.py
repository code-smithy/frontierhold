from fastapi import APIRouter

from game.state import GameState

router = APIRouter()


def get_state_dependency() -> GameState:
    raise NotImplementedError("State dependency must be overridden by main app")


@router.get("/state")
def get_state() -> dict:
    return get_state_dependency().to_dict()
