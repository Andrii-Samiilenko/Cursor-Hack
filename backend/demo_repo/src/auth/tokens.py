"""JWT-like token utilities (simplified demo)."""


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
