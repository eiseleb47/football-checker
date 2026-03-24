#!/usr/bin/env python3
"""
Football Checker — Desktop GUI

Starts the Flask server on a free local port and displays it inside a
native Qt desktop window (PySide6 + QtWebEngine).

No system packages are required beyond a normal pip install.
"""
from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP_TITLE = "Football Checker"


# ── Dependency check ──────────────────────────────────────────────────────────

try:
    from PySide6.QtCore import QSize, QTimer, QUrl
    from PySide6.QtGui import QIcon
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import QApplication, QMainWindow
except ImportError:
    print(
        "PySide6 is required for the desktop GUI.\n"
        "\n"
        "Install it with:\n"
        f"  {os.path.join(HERE, '.venv', 'bin', 'pip')} install PySide6\n"
        "\n"
        "(One-time download ~250 MB; includes Qt WebEngine.)\n",
        file=sys.stderr,
    )
    sys.exit(1)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _free_port() -> int:
    """Return an unused TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _flask_cmd(port: int) -> list[str]:
    venv_python = os.path.join(HERE, ".venv", "bin", "python")
    python = venv_python if os.path.isfile(venv_python) else sys.executable
    return [python, os.path.join(HERE, "app.py")]


def _loading_html() -> str:
    """Animated splash shown in the WebView while Flask starts up."""
    return """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: #0d1b2a;
  color: #f0f0f0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  font-family: system-ui, -apple-system, sans-serif;
  user-select: none;
}
.icon {
  font-size: 80px;
  margin-bottom: 24px;
  animation: pulse 2.6s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { transform: scale(1);    opacity: 1;   }
  50%       { transform: scale(1.07); opacity: 0.72; }
}
h1 {
  font-size: 1.75em;
  font-weight: 600;
  letter-spacing: 0.03em;
  margin-bottom: 6px;
}
.sub {
  color: #4a90d9;
  font-size: 0.92em;
  margin-bottom: 40px;
}
.bar {
  width: 210px;
  height: 4px;
  background: #1a2e44;
  border-radius: 2px;
  overflow: hidden;
}
.fill {
  height: 100%;
  background: linear-gradient(90deg, #1a6b3a, #3ddc84);
  animation: sweep 1.8s ease-in-out infinite;
}
@keyframes sweep {
  0%    { transform: scaleX(0);   transform-origin: left;  }
  49%   { transform: scaleX(1);   transform-origin: left;  }
  50%   { transform: scaleX(1);   transform-origin: right; }
  100%  { transform: scaleX(0);   transform-origin: right; }
}
</style>
</head>
<body>
  <div class="icon">⚽</div>
  <h1>Football Checker</h1>
  <div class="sub">Bundesliga Live Scores &amp; Tables</div>
  <div class="bar"><div class="fill"></div></div>
</body>
</html>"""


# ── Main window ───────────────────────────────────────────────────────────────

class FootballWindow(QMainWindow):
    """Main application window: shows a loading page, then Flask."""

    def __init__(self, port: int) -> None:
        super().__init__()
        self._port = port

        self.setWindowTitle(APP_TITLE)
        self.resize(1280, 860)
        self.setMinimumSize(QSize(900, 600))

        icon_path = os.path.join(HERE, "assets", "icon.svg")
        if os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._view = QWebEngineView()
        self._view.setHtml(_loading_html(), QUrl("http://localhost/"))
        self.setCentralWidget(self._view)

        # Poll every 300 ms until Flask is accepting connections
        self._poll = QTimer(self)
        self._poll.setInterval(300)
        self._poll.timeout.connect(self._check_server)
        self._poll.start()

    def _check_server(self) -> None:
        try:
            with socket.create_connection(("127.0.0.1", self._port), timeout=0.1):
                self._poll.stop()
                self._view.load(QUrl(f"http://127.0.0.1:{self._port}"))
        except OSError:
            pass  # Not ready yet; keep polling


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    # Let Ctrl-C in the terminal actually terminate the app
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Disable the sandbox in the QtWebEngine GPU process (avoids permission
    # errors in some Linux environments without affecting security meaningfully
    # for a local-only server).
    os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("Football Checker")
    app.setOrganizationName("FootballChecker")

    icon_path = os.path.join(HERE, "assets", "icon.svg")
    if os.path.isfile(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    port = _free_port()
    env = os.environ.copy()
    env["PORT"] = str(port)
    env["FLASK_HOST"] = "127.0.0.1"

    proc = subprocess.Popen(
        _flask_cmd(port),
        cwd=HERE,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    def _cleanup() -> None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    app.aboutToQuit.connect(_cleanup)

    window = FootballWindow(port)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
