"""Start a local server with a temporary database for each browser test."""
import socket
import threading
import time

import pytest
import uvicorn
from app.main import create_app


@pytest.fixture
def live_url(tmp_path):
    # Port 0 lets the OS select a free port without colliding with the manual app.
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(create_app(tmp_path / "browser.db"), log_level="error"))
    thread = threading.Thread(target=server.run, kwargs={"sockets":[sock]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 15
        while not server.started:
            if not thread.is_alive() or time.monotonic() > deadline:
                raise RuntimeError("Test server did not start")
            time.sleep(0.05)
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()
