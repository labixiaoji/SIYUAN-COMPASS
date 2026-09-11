from __future__ import annotations

from dataclasses import dataclass
import hmac
from typing import Any
from urllib.parse import urlencode, urlsplit

import httpx
import jwt
from jwt import InvalidTokenError

from app.core.config import get_settings


class JAccountOAuthError(Exception):
    """A safe, non-sensitive jAccount OAuth failure."""


@dataclass(frozen=True)
class JAccountIdentity:
    username: str
    display_name: str


def build_authorization_url(*, state: str, nonce: str) -> str:
    settings = get_settings()
    parsed = urlsplit(settings.jaccount_authorize_url)
    redirect = urlsplit(settings.jaccount_redirect_uri or "")
    if parsed.scheme != "https" or redirect.scheme not in {"http", "https"}:
        raise JAccountOAuthError("invalid_oauth_configuration")

    separator = "&" if parsed.query else "?"
    return f"{settings.jaccount_authorize_url}{separator}{urlencode({
        'response_type': 'code',
        'scope': settings.jaccount_scope,
        'client_id': settings.jaccount_client_id,
        'redirect_uri': settings.jaccount_redirect_uri,
        'state': state,
        'nonce': nonce,
    })}"


async def exchange_authorization_code(code: str) -> dict[str, Any]:
    settings = get_settings()
    if urlsplit(settings.jaccount_token_url).scheme != "https":
        raise JAccountOAuthError("invalid_token_endpoint")

    try:
        async with httpx.AsyncClient(timeout=settings.jaccount_http_timeout_seconds) as client:
            response = await client.post(
                settings.jaccount_token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.jaccount_redirect_uri,
                },
                auth=(
                    settings.jaccount_client_id, 
                    settings.jaccount_client_secret
                    ),
                headers={"Accept": "application/json"},
            )
    except httpx.HTTPError as exc:
        raise JAccountOAuthError("token_endpoint_unavailable") from exc

    if response.status_code != 200:
        raise JAccountOAuthError(f"token_exchange_rejected:{response.status_code}")

    try:
        payload = response.json()
    except ValueError as exc:
        raise JAccountOAuthError("invalid_token_response") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("id_token"), str):
        raise JAccountOAuthError("missing_id_token")
    return payload


def decode_identity_token(id_token: str, *, expected_nonce: str) -> JAccountIdentity:
    settings = get_settings()
    try:
        claims = jwt.decode(
            id_token,
            settings.jaccount_client_secret,
            algorithms=["HS256"],
            audience=settings.jaccount_client_id,
            issuer=settings.jaccount_issuer,
            options={"require": ["iss", "sub", "aud", "exp", "iat", "nonce"]},
        )
    except InvalidTokenError as exc:
        raise JAccountOAuthError("invalid_id_token") from exc

    nonce = claims.get("nonce")
    if not isinstance(nonce, str) or not hmac.compare_digest(nonce, expected_nonce):
        raise JAccountOAuthError("nonce_mismatch")

    username = str(claims.get("sub") or "").strip().lower()
    if not username:
        raise JAccountOAuthError("missing_subject")
    display_name = str(claims.get("name") or username).strip()
    return JAccountIdentity(username=username, display_name=display_name or username)
