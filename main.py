from __future__ import annotations

import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from api.routes import assign_workers, build, get_state
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
    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (std lib method name)
        route = urlparse(self.path).path
        if route == "/state":
            self._send_json(200, get_state(state))
            return

        if route == "/":
            self.path = "/static/index.html"
        elif route.startswith("/static/"):
            self.path = route

        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        route = urlparse(self.path).path
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length else b"{}"
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON payload"})
            return

        try:
            if route == "/assign_workers":
                self._send_json(200, assign_workers(state, payload))
                return
            if route == "/build":
                self._send_json(200, build(state, payload))
                return
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
            return

        self._send_json(404, {"error": "Unknown endpoint"})

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
