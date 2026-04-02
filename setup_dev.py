#!/usr/bin/env python3
"""First-time setup: backend venv + pip, frontend npm install. Run from repo root."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def _npm_on_path() -> bool:
    if sys.platform == "win32":
        try:
            r = subprocess.run(
                "where npm",
                shell=True,
                capture_output=True,
                text=True,
            )
            return r.returncode == 0
        except OSError:
            return False
    return shutil.which("npm") is not None


def _run_npm_install() -> None:
    """Windows: use shell so `npm.cmd` resolves (list form often gives WinError 2)."""
    if sys.platform == "win32":
        subprocess.run("npm install", cwd=FRONTEND, shell=True, check=True)
    else:
        npm = shutil.which("npm")
        if not npm:
            raise FileNotFoundError("npm")
        subprocess.run([npm, "install"], cwd=FRONTEND, check=True)


def main() -> None:
    if not _npm_on_path():
        print(
            "npm не найден. Установи Node.js LTS: https://nodejs.org/\n"
            "Закрой и снова открой терминал, затем: python setup_dev.py"
        )
        sys.exit(1)

    venv_dir = BACKEND / ".venv"
    if not venv_dir.is_dir():
        print("[setup] Creating backend/.venv …")
        subprocess.run([sys.executable, "-m", "venv", ".venv"], cwd=BACKEND, check=True)
    else:
        print("[setup] backend/.venv already exists — skipping venv create")

    if sys.platform == "win32":
        py = BACKEND / ".venv" / "Scripts" / "python.exe"
        pip = [str(py), "-m", "pip"]
    else:
        py = BACKEND / ".venv" / "bin" / "python"
        pip = [str(py), "-m", "pip"]

    print("[setup] pip install -r backend/requirements.txt …")
    subprocess.run([*pip, "install", "--upgrade", "pip"], check=True)
    subprocess.run([*pip, "install", "-r", str(BACKEND / "requirements.txt")], check=True)

    print("[setup] npm install in frontend/ …")
    try:
        _run_npm_install()
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(
            "Не удалось выполнить npm install. Проверь, что Node.js установлен и команда `npm` работает в этом терминале.\n"
            f"Детали: {e}"
        )
        sys.exit(1)

    print()
    print("Done. Start everything with:  python run_dev.py")
    print()


if __name__ == "__main__":
    main()
