import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Dict, Tuple


class FakeInferHandler(BaseHTTPRequestHandler):
    """Mutable class-level response for unit tests."""

    response_body: Dict[str, Any] = {"action": [0.0] * 7, "latency_ms": 1.0}
    status_code: int = 200

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        _ = self.rfile.read(length)
        body = json.dumps(self.response_body).encode("utf-8")
        self.send_response(self.status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:  # noqa: ARG002
        return


def start_fake_infer_server() -> Tuple[str, Callable[[], None]]:
    server = HTTPServer(("127.0.0.1", 0), FakeInferHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    url = f"http://{host}:{port}/infer"

    def shutdown() -> None:
        server.shutdown()
        thread.join(timeout=5)

    return url, shutdown
