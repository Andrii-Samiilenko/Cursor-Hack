#!/usr/bin/env python3
"""
One terminal: FastAPI (reload) + Vite dev server.
Usage (from repo root):  python run_dev.py
Requires: backend/.venv with deps, npm + frontend/node_modules (auto npm install if missing).
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def venv_python() -> Path | None:
    if sys.platform == "win32":
        p = BACKEND / ".venv" / "Scripts" / "python.exe"
    else:
        p = BACKEND / ".venv" / "bin" / "python"
    return p if p.exists() else None


def stream_output(prefix: str, proc: subprocess.Popen[str]) -> None:
    assert proc.stdout is not None
    try:
        for line in iter(proc.stdout.readline, ""):
            if line == "" and proc.poll() is not None:
                break
            if line:
                sys.stdout.write(f"[{prefix}] {line}")
                sys.stdout.flush()
    except Exception:
        pass


def main() -> None:
    py = venv_python()
    if not py:
        print(
            "Missing backend/.venv — run once from repo root:\n"
            "  python setup_dev.py\n"
            "or manually: cd backend && python -m venv .venv && .venv\\Scripts\\python -m pip install -r requirements.txt"
        )
        sys.exit(1)

    def _npm_ok() -> bool:
        if sys.platform == "win32":
            try:
                r = subprocess.run("where npm", shell=True, capture_output=True, text=True)
                return r.returncode == 0
            except OSError:
                return False
        return shutil.which("npm") is not None

    if not _npm_ok():
        print("npm not found. Install Node.js from https://nodejs.org/ and reopen the terminal.")
        sys.exit(1)

    if not (FRONTEND / "node_modules").exists():
        print("[ui] Installing frontend dependencies (npm install)…")
        if sys.platform == "win32":
            subprocess.run("npm install", cwd=FRONTEND, shell=True, check=True)
        else:
            subprocess.run(["npm", "install"], cwd=FRONTEND, check=True)

    env = os.environ.copy()
    # Stable UTF-8 logs on Windows consoles when possible
    env.setdefault("PYTHONUTF8", "1")

    api = subprocess.Popen(
        [str(py), "-m", "uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
        cwd=BACKEND,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )
    if sys.platform == "win32":
        ui = subprocess.Popen(
            "npm run dev -- --host 127.0.0.1 --port 5173",
            cwd=FRONTEND,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
            shell=True,
        )
    else:
        ui = subprocess.Popen(
            ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
            cwd=FRONTEND,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )

    procs: list[subprocess.Popen[str]] = [api, ui]

    threading.Thread(target=stream_output, args=("api", api), daemon=True).start()
    threading.Thread(target=stream_output, args=("ui", ui), daemon=True).start()

    print()
    print("  Context Surgeon — dev")
    print("  UI (use this):  http://127.0.0.1:5173")
    print("  API:            http://127.0.0.1:8000")
    print("  Ctrl+C stops both.")
    print()

    def shutdown(*_args: object) -> None:
        for p in procs:
            if p.poll() is None:
                p.terminate()
        time.sleep(0.5)
        for p in procs:
            if p.poll() is None:
                p.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    # Exit when first child dies (e.g. uvicorn crash)
    try:
        while True:
            time.sleep(0.3)
            if api.poll() is not None:
                print(f"[api] process exited ({api.returncode})")
                shutdown()
            if ui.poll() is not None:
                print(f"[ui] process exited ({ui.returncode})")
                shutdown()
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
