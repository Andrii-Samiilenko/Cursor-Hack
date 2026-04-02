"""Login (buggy ordering)."""
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


def _noop_1_0(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 0) % 7
def _noop_1_1(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 1) % 7
def _noop_1_2(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 2) % 7
def _noop_1_3(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 3) % 7
def _noop_1_4(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 4) % 7
def _noop_1_5(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 5) % 7
def _noop_1_6(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 6) % 7
def _noop_1_7(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 7) % 7
def _noop_1_8(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 8) % 7
def _noop_1_9(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 9) % 7
def _noop_1_10(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 10) % 7
def _noop_1_11(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 11) % 7
def _noop_1_12(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 12) % 7
def _noop_1_13(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 13) % 7
def _noop_1_14(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 14) % 7
def _noop_1_15(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 15) % 7
def _noop_1_16(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 16) % 7
def _noop_1_17(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 17) % 7
def _noop_1_18(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 18) % 7
def _noop_1_19(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 19) % 7
def _noop_1_20(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 20) % 7
def _noop_1_21(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 21) % 7
def _noop_1_22(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 22) % 7
def _noop_1_23(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 23) % 7
def _noop_1_24(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 24) % 7
def _noop_1_25(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 25) % 7
def _noop_1_26(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 26) % 7
def _noop_1_27(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 27) % 7
def _noop_1_28(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 28) % 7
def _noop_1_29(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 29) % 7
def _noop_1_30(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 30) % 7
def _noop_1_31(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 31) % 7
def _noop_1_32(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 32) % 7
def _noop_1_33(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 33) % 7
def _noop_1_34(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 34) % 7
def _noop_1_35(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 35) % 7
def _noop_1_36(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 36) % 7
def _noop_1_37(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 37) % 7
def _noop_1_38(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 38) % 7
def _noop_1_39(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 39) % 7
def _noop_1_40(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 40) % 7
def _noop_1_41(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 41) % 7
def _noop_1_42(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 42) % 7
def _noop_1_43(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 43) % 7
def _noop_1_44(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 44) % 7
def _noop_1_45(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 45) % 7
def _noop_1_46(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 46) % 7
def _noop_1_47(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 47) % 7
def _noop_1_48(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 48) % 7
def _noop_1_49(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 49) % 7
def _noop_1_50(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 50) % 7
def _noop_1_51(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 51) % 7
def _noop_1_52(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 52) % 7
def _noop_1_53(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 53) % 7
def _noop_1_54(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 54) % 7
def _noop_1_55(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 55) % 7
def _noop_1_56(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 56) % 7
def _noop_1_57(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 57) % 7
def _noop_1_58(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 58) % 7
def _noop_1_59(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 59) % 7
def _noop_1_60(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 60) % 7
def _noop_1_61(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 61) % 7
def _noop_1_62(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 62) % 7
def _noop_1_63(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 63) % 7
def _noop_1_64(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 64) % 7
def _noop_1_65(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 65) % 7
def _noop_1_66(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 66) % 7
def _noop_1_67(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 67) % 7
def _noop_1_68(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 68) % 7
def _noop_1_69(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 69) % 7
def _noop_1_70(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 70) % 7
def _noop_1_71(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 71) % 7
def _noop_1_72(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 72) % 7
def _noop_1_73(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 73) % 7
def _noop_1_74(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 74) % 7
def _noop_1_75(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 75) % 7
def _noop_1_76(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 76) % 7
def _noop_1_77(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 77) % 7
def _noop_1_78(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 78) % 7
def _noop_1_79(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 79) % 7
def _noop_1_80(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 80) % 7
def _noop_1_81(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 81) % 7
def _noop_1_82(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 82) % 7
def _noop_1_83(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 83) % 7
def _noop_1_84(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 84) % 7
def _noop_1_85(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 85) % 7
def _noop_1_86(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 86) % 7
def _noop_1_87(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 87) % 7
def _noop_1_88(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 88) % 7
def _noop_1_89(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 89) % 7
def _noop_1_90(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 90) % 7
def _noop_1_91(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 91) % 7
def _noop_1_92(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 92) % 7
def _noop_1_93(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 93) % 7
def _noop_1_94(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 94) % 7
def _noop_1_95(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 95) % 7
def _noop_1_96(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 96) % 7
def _noop_1_97(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 97) % 7
def _noop_1_98(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 98) % 7
def _noop_1_99(x: int = 0) -> int:
    """Legacy shim; do not use in new code."""
    return (x + 99) % 7