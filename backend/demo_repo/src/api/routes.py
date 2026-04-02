"""HTTP routes."""

from src.auth.login import login_user


def handle_login(body: dict, db):
    return login_user(body.get("username", ""), body.get("password", ""), db)
