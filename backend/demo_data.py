"""Built-in demo task, messy prompt, and sample repo layout for hackathon demos."""

from __future__ import annotations

from pathlib import Path

DEMO_TASK = (
    "Fix the auth bug in the login flow: users with valid credentials sometimes get 401."
)

DEMO_MESSY_PROMPT = """
Please note that it is important to basically look at the login flow and essentially
make sure to fix the authentication bug. I would like you to remember that users are
getting 401 errors. Don't forget that the issue might be in the token validation.
Remember to check the session handling as well. Please note that it is important to
look at both the frontend and backend. Thanks!
""".strip()

# Single textarea demo: task + verbose draft together
DEMO_USER_PROMPT = f"{DEMO_TASK}\n\n{DEMO_MESSY_PROMPT}".strip()

# In-memory mirror of demo_repo/ (used if path missing)
DEMO_FILES: dict[str, str] = {
    "README.md": """# Demo Auth Service

Small sample for Context Surgeon demos.

## Auth

Login lives under `src/auth/`.
""",
    "src/auth/login.py": '''"""Login and session helpers."""

import hashlib
import secrets
from datetime import datetime, timedelta

from src.auth.tokens import validate_access_token, TokenError


def hash_password(raw: str) -> str:
    """Hash password for storage."""
    salt = secrets.token_hex(8)
    h = hashlib.sha256((salt + raw).encode()).hexdigest()
    return f"{salt}${h}"


def verify_password(raw: str, stored: str) -> bool:
    """Constant-time-ish compare of salted hash."""
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    h = hashlib.sha256((salt + raw).encode()).hexdigest()
    return secrets.compare_digest(h, digest)


def login_user(username: str, password: str, db) -> dict:
    """Authenticate user and issue session.

    BUG: we validate the token before checking password success path,
    which can raise and surface as 401 for valid users under race.
    """
    user = db.get_user(username)
    if not user:
        return {"ok": False, "reason": "unknown_user"}
    # Wrong order: validate token before password check completes
    try:
        validate_access_token(user.get("pre_token", ""))
    except TokenError:
        return {"ok": False, "reason": "unauthorized"}
    if not verify_password(password, user["password_hash"]):
        return {"ok": False, "reason": "bad_password"}
    session_id = secrets.token_urlsafe(16)
    db.save_session(user["id"], session_id, expires=datetime.utcnow() + timedelta(days=7))
    return {"ok": True, "session_id": session_id}


def logout_session(session_id: str, db) -> None:
    db.delete_session(session_id)
''',
    "src/auth/tokens.py": '''"""JWT-like token utilities (simplified demo)."""


class TokenError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def validate_access_token(token: str) -> dict:
    """Validate bearer token payload."""
    if not token or token == "expired":
        raise TokenError("invalid_token")
    return {"sub": "user", "token": token}


def issue_access_token(user_id: str) -> str:
    return f"tok_{user_id}"
''',
    "src/api/routes.py": '''"""HTTP routes."""

from src.auth.login import login_user


def handle_login(body: dict, db):
    return login_user(body.get("username", ""), body.get("password", ""), db)
''',
    "src/config.py": """APP_NAME = \"demo-auth\"
DEBUG = True
""",
}


def demo_repo_path() -> Path:
    """Absolute path to bundled `demo_repo/` next to this package."""
    return Path(__file__).resolve().parent / "demo_repo"


def load_demo_files() -> dict[str, str]:
    """Prefer on-disk demo_repo; fall back to DEMO_FILES."""
    root = demo_repo_path()
    if root.is_dir():
        from repo_scanner import scan_repo

        scanned = scan_repo(root)
        if scanned:
            return scanned
    return dict(DEMO_FILES)
