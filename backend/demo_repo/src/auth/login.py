"""Login and session helpers."""

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
