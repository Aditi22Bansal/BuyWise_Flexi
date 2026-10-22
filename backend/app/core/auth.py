"""Lightweight local authentication for the BuyWise demo.

Accounts are defined in code because this project is a self-contained demo.
Tokens are short-lived HMAC-signed values, so no extra dependencies are needed.
"""

import base64
import hashlib
import hmac
import json
import time
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

TOKEN_TTL_SECONDS = 12 * 60 * 60

ACCOUNTS = {
    "owner": {
        "password": "owner-pass-123",
        "name": "Admin Owner",
        "role": "admin",
        "title": "Administrator",
        "description": "Manages accounts and every part of the platform",
        "approval_limit": None,
    },
    "req.alice": {
        "password": "alice-pass-1",
        "name": "Alice Requester",
        "role": "requester",
        "title": "Requester",
        "description": "Creates procurement requests",
        "approval_limit": 0,
    },
    "off.bob": {
        "password": "bob-pass-22",
        "name": "Bob Officer",
        "role": "officer",
        "title": "Procurement Officer",
        "description": "Runs the agent pipeline and demo",
        "approval_limit": 0,
    },
    "app.cara": {
        "password": "cara-pass-33",
        "name": "Cara Approver",
        "role": "approver",
        "title": "Approver",
        "description": "Approves up to 500,000",
        "approval_limit": 500000,
    },
    "aud.dan": {
        "password": "dan-pass-44",
        "name": "Dan Auditor",
        "role": "auditor",
        "title": "Auditor",
        "description": "View only access to requests, logs and results",
        "approval_limit": 0,
    },
}

ROLE_LABELS = {
    "admin": "Admin",
    "requester": "Requester",
    "officer": "Officer",
    "approver": "Approver",
    "auditor": "Auditor",
}


def public_user(username: str) -> dict:
    account = ACCOUNTS[username]
    return {
        "username": username,
        "name": account["name"],
        "role": account["role"],
        "role_label": ROLE_LABELS.get(account["role"], account["role"]),
        "title": account["title"],
        "description": account["description"],
        "approval_limit": account["approval_limit"],
    }


def authenticate(username: str, password: str) -> Optional[dict]:
    account = ACCOUNTS.get(username)
    if not account:
        return None
    if not hmac.compare_digest(account["password"], password):
        return None
    return public_user(username)


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    body = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"), body.encode("ascii"), hashlib.sha256
    ).digest()
    return f"{body}.{_b64encode(signature)}"


def decode_access_token(token: str) -> Optional[str]:
    try:
        body, signature = token.split(".", 1)
        expected = hmac.new(
            settings.SECRET_KEY.encode("utf-8"), body.encode("ascii"), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(_b64decode(signature), expected):
            return None
        payload = json.loads(_b64decode(body).decode("utf-8"))
        if payload.get("exp", 0) < int(time.time()):
            return None
        username = payload.get("sub")
        return username if username in ACCOUNTS else None
    except Exception:
        return None


_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    token = None
    if credentials is not None and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
    elif request.query_params.get("token"):
        # EventSource cannot set Authorization headers, so SSE may pass a token
        # as a query parameter.
        token = request.query_params.get("token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = decode_access_token(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return public_user(username)


def require_roles(*roles: str):
    def dependency(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your role ({user['role_label']}) cannot perform this action",
            )
        return user

    return dependency
