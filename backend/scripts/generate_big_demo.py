"""One-off generator for demo_repo_big (large noisy repo for hackathon metrics). Run from repo: python backend/scripts/generate_big_demo.py"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "demo_repo_big"

NOISE = '''
def _noop_{n}_{i}(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + {i}) % 7

'''.strip()


def chunk_noise(n: int, lines: int = 120) -> str:
    parts = []
    for i in range(lines):
        parts.append(NOISE.format(n=n, i=i))
    return "\n".join(parts)


FILES: dict[str, str] = {}

FILES["README.md"] = """# BigDemo Monolith (stress test)

Internal dashboard + auth stack. Lots of legacy modules; most are irrelevant to any single bugfix.

## Areas

- `src/auth/` — login, tokens, session
- `src/api/` — HTTP handlers
- `src/dashboard/` — widgets (usage charts)
- `src/legacy/` — deprecated batch jobs

If you only need to fix **login / 401**, you should not load the entire tree into the LLM.
"""

# Core bug file (same idea as small demo)
FILES["src/auth/login.py"] = '''"""Login (buggy ordering)."""
import hashlib
import secrets
from datetime import datetime, timedelta

from src.auth.tokens import validate_access_token, TokenError


def hash_password(raw: str) -> str:
    salt = secrets.token_hex(8)
    h = hashlib.sha256((salt + raw).encode()).hexdigest()
    return f"{salt}${h}"


def verify_password(raw: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    h = hashlib.sha256((salt + raw).encode()).hexdigest()
    return secrets.compare_digest(h, digest)


def login_user(username: str, password: str, db) -> dict:
    """BUG: validates token before password path; valid users may see 401."""
    user = db.get_user(username)
    if not user:
        return {"ok": False, "reason": "unknown_user"}
    try:
        validate_access_token(user.get("pre_token", ""))
    except TokenError:
        return {"ok": False, "reason": "unauthorized"}
    if not verify_password(password, user["password_hash"]):
        return {"ok": False, "reason": "bad_password"}
    session_id = secrets.token_urlsafe(16)
    db.save_session(user["id"], session_id, expires=datetime.utcnow() + timedelta(days=7))
    return {"ok": True, "session_id": session_id}
''' + "\n\n" + chunk_noise(1, 100)

FILES["src/auth/tokens.py"] = '''"""Token helpers."""
class TokenError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

def validate_access_token(token: str) -> dict:
    if not token or token == "expired":
        raise TokenError("invalid_token")
    return {"sub": "user", "token": token}

def issue_access_token(user_id: str) -> str:
    return f"tok_{user_id}"
''' + "\n\n" + chunk_noise(2, 90)

FILES["src/auth/session_store.py"] = (
    '''"""Redis-like session API (stub)."""
from typing import Any

def save_session(user_id: str, sid: str, ttl: int = 3600) -> None:
    pass

def load_session(sid: str) -> dict[str, Any] | None:
    return None
'''
    + "\n\n"
    + chunk_noise(3, 110)
)

for name, n in [
    ("src/api/auth_routes.py", 4),
    ("src/api/user_routes.py", 5),
    ("src/api/admin_routes.py", 6),
    ("src/api/dashboard_routes.py", 7),
    ("src/dashboard/widgets.py", 8),
    ("src/dashboard/usage_heatmap.py", 9),
    ("src/models/user.py", 10),
    ("src/models/billing.py", 11),
    ("src/services/email_worker.py", 12),
    ("src/services/audit_log.py", 13),
    ("src/legacy/batch_import.py", 14),
    ("src/legacy/reporting_jobs.py", 15),
]:
    FILES[name] = f'"""Generated module — not all code paths are used."""\n\n' + chunk_noise(n, 95)


def main() -> None:
    for rel, body in FILES.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    print(f"Wrote {len(FILES)} files under {ROOT}")


if __name__ == "__main__":
    main()
