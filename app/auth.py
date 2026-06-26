"""
auth.py - Lightweight HMAC-signed cookie sessions.
No external dependencies beyond Python stdlib.

Roles:
    "admin"  — full access (refresh, override, ad-hoc roster)
    "viewer" — read-only (default, no login required)
"""
import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime

from fastapi import Request
from fastapi.responses import Response

from config import (
    SESSION_SECRET,
    ADMIN_USERNAME,
    ADMIN_PASSWORD_HASH,
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECS,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Low-level signing
# ---------------------------------------------------------------------------
def _sign(payload: str) -> str:
    sig = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def _verify(token: str) -> str | None:
    try:
        payload, sig = token.rsplit(".", 1)
        expected = hmac.new(
            SESSION_SECRET.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        if hmac.compare_digest(sig, expected):
            return payload
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def check_credentials(username: str, password: str) -> bool:
    """Return True if username + password match admin credentials."""
    u_ok = hmac.compare_digest(username.strip(), ADMIN_USERNAME)
    p_hash = hashlib.sha256(password.encode()).hexdigest()
    p_ok = hmac.compare_digest(p_hash, ADMIN_PASSWORD_HASH)
    return u_ok and p_ok


def set_session(response: Response, role: str = "admin") -> None:
    """Write a signed session cookie onto response."""
    data = base64.b64encode(
        json.dumps({"role": role, "ts": datetime.utcnow().isoformat()}).encode()
    ).decode()
    token = _sign(data)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        httponly=True,
        max_age=SESSION_MAX_AGE_SECS,
        samesite="lax",
    )


def clear_session(response: Response) -> None:
    """Delete the session cookie."""
    response.delete_cookie(SESSION_COOKIE_NAME)


def get_role(request: Request) -> str:
    """Return 'admin' or 'viewer' based on the session cookie."""
    token = request.cookies.get(SESSION_COOKIE_NAME, "")
    if not token:
        return "viewer"
    payload = _verify(token)
    if not payload:
        return "viewer"
    try:
        data = json.loads(base64.b64decode(payload).decode())
        return data.get("role", "viewer")
    except Exception:
        return "viewer"


def is_admin(request: Request) -> bool:
    return get_role(request) == "admin"
