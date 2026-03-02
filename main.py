from __future__ import annotations

import json
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from api.routes import get_state
from game import engine
from game.state import GameState

ROOT = Path(__file__).parent
STATIC_DIR = ROOT / "static"

state = GameState()


def tick_loop(stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        engine.tick(state)
        stop_event.wait(1)


class FrontierHoldHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (std lib method name)
        route = urlparse(self.path).path
        if route == "/state":
            payload = json.dumps(get_state(state)).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if route == "/":
            self.path = "/static/index.html"
        elif route.startswith("/static/"):
            self.path = route

        return super().do_GET()

    def translate_path(self, path: str) -> str:
        route = urlparse(path).path
        if route.startswith("/static/"):
            relative = route.removeprefix("/static/")
            return str((STATIC_DIR / relative).resolve())
        return str((ROOT / route.lstrip("/")).resolve())


def run() -> None:
    stop_event = threading.Event()
    ticker = threading.Thread(target=tick_loop, args=(stop_event,), daemon=True)
    ticker.start()

    server = ThreadingHTTPServer(("0.0.0.0", 8000), FrontierHoldHandler)
    try:
        print("Frontier Hold running at http://127.0.0.1:8000")
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        server.server_close()


if __name__ == "__main__":
    run()
