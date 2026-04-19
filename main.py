"""
main.py  –  Desktop entry point
Starts the FastAPI server in a background thread, then opens a native
pywebview window. Closing the window shuts down the server.
"""
import threading
import time
import socket
import sys
import os

# ── Make sure relative imports (data/, models/, templates/) work when
#    bundled by PyInstaller (sys._MEIPASS) or run directly.
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS          # PyInstaller temp-extract dir
    # Also set cwd to the folder that contains the .exe so that
    # data/ and models/ written at runtime land next to the executable.
    os.chdir(os.path.dirname(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    os.chdir(BASE_DIR)

# Patch template / static lookup before importing app
import app as fastapi_app          # noqa: E402  (our app.py)
fastapi_app.templates = __import__(
    'fastapi.templating', fromlist=['Jinja2Templates']
).Jinja2Templates(directory=os.path.join(BASE_DIR, 'templates'))

import uvicorn                     # noqa: E402
import webview                     # noqa: E402


# ── Pick a free port ──────────────────────────────────────────────────────────

def _free_port() -> int:
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


PORT = _free_port()
URL  = f'http://127.0.0.1:{PORT}'


# ── Server thread ─────────────────────────────────────────────────────────────

def _run_server():
    uvicorn.run(
        fastapi_app.app,
        host='127.0.0.1',
        port=PORT,
        log_level='error',
    )


server_thread = threading.Thread(target=_run_server, daemon=True)
server_thread.start()


# ── Wait until the server is actually accepting connections ───────────────────

def _wait_for_server(timeout: float = 15.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(('127.0.0.1', PORT), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError('FastAPI server did not start in time.')


_wait_for_server()


# ── Open the native window ────────────────────────────────────────────────────

window = webview.create_window(
    title='CrudeAI – Asphaltene Predictor',
    url=URL,
    width=1280,
    height=820,
    min_size=(900, 600),
    resizable=True,
)

# Use the EdgeChromium (WebView2) renderer on Windows for best compatibility
webview.start(gui='edgechromium')
