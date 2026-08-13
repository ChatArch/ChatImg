from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

DEFAULT_OPENAI_OAUTH_BASE_URL = "https://auth.openai.com"
CODEX_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
CODEX_OAUTH_SCOPE = "openid profile email"


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _token_url_from_base(base_url: str) -> str:
    return f"{base_url.strip().rstrip('/')}/oauth/token"


def refresh_codex_oauth_token(
    refresh_token: str,
    *,
    client_id: str = CODEX_CLIENT_ID,
    base_url: str | None = None,
    scope: str = CODEX_OAUTH_SCOPE,
    timeout_seconds: float = 20.0,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Exchange a Codex OAuth refresh token for a fresh access token.

    Returns normalized OpenAI OAuth token metadata. The refresh token is opaque;
    the authoritative expiry comes from the OAuth token endpoint's
    ``expires_in`` response.
    """
    refresh_token = (refresh_token or "").strip()
    if not refresh_token:
        raise ValueError("refresh_token is required")

    refreshed_at = now or datetime.now(timezone.utc)
    resolved_base_url = base_url or DEFAULT_OPENAI_OAUTH_BASE_URL
    resolved_token_url = _token_url_from_base(resolved_base_url)
    timeout = httpx.Timeout(max(5.0, float(timeout_seconds)))
    with httpx.Client(timeout=timeout, headers={"Accept": "application/json"}) as client:
        response = client.post(
            resolved_token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "scope": scope,
            },
        )

    if response.status_code != 200:
        raise RuntimeError(f"Codex OAuth token refresh failed with status {response.status_code}")

    payload = response.json()
    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        raise RuntimeError("Codex OAuth refresh response was missing access_token")

    next_refresh = payload.get("refresh_token")
    if not isinstance(next_refresh, str) or not next_refresh.strip():
        next_refresh = refresh_token

    expires_in = int(payload.get("expires_in") or 3600)
    expires_at = refreshed_at + timedelta(seconds=expires_in)

    result: dict[str, Any] = {
        "access_token": access_token.strip(),
        "refresh_token": next_refresh.strip(),
        "access_token_expires_at": _iso_z(expires_at),
    }
    id_token = payload.get("id_token")
    if isinstance(id_token, str) and id_token.strip():
        result["id_token"] = id_token.strip()
    return result
