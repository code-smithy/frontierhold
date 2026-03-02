from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api import routes
from game import engine
from game.state import GameState

state = GameState()


def _state_dependency() -> GameState:
    return state


routes.get_state_dependency = _state_dependency


async def tick_loop() -> None:
    while True:
        engine.tick(state)
        await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(tick_loop())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="Frontier Hold", lifespan=lifespan)
app.include_router(routes.router)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse("static/index.html")
