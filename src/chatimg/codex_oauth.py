from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import dotenv_values

from chatimg.config import CodexConfig

CODEX_OAUTH_BASE_URL = "https://auth.openai.com"
CODEX_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
CODEX_OAUTH_SCOPE = "openid profile email"


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _token_url_from_base(base_url: str) -> str:
    return f"{base_url.strip().rstrip('/')}/oauth/token"


def _present(value: str | None) -> str:
    return "present" if (value or "").strip() else "missing"


def build_codex_oauth_status(*, env_file: str | Path | None = None) -> dict[str, str]:
    """Return safe Codex OAuth token metadata without secret values."""
    return {
        "access_token": _present(CodexConfig.CODEX_ACCESS_TOKEN.value),
        "refresh_token": _present(CodexConfig.CODEX_REFRESH_TOKEN.value),
        "oauth_base_url": str(CodexConfig.CODEX_OAUTH_BASE_URL.value or ""),
        "access_token_expires_at": str(CodexConfig.CODEX_ACCESS_TOKEN_EXPIRES_AT.value or ""),
        "env_file": str(env_file) if env_file is not None else "",
    }


def build_codex_oauth_refresh_result(
    *,
    token_data: dict[str, Any],
    oauth_base_url: str,
    saved: bool,
    env_file: str | Path | None = None,
) -> dict[str, Any]:
    """Return safe refresh result metadata without secret token values."""
    return {
        "access_token": _present(str(token_data.get("access_token") or "")),
        "refresh_token": _present(str(token_data.get("refresh_token") or "")),
        "oauth_base_url": oauth_base_url,
        "access_token_expires_at": str(token_data.get("access_token_expires_at") or ""),
        "saved": saved,
        "env_file": str(env_file) if env_file is not None else None,
    }


def save_codex_oauth_token_data(
    *,
    token_data: dict[str, Any],
    oauth_base_url: str,
    target_path: str | Path,
) -> Path:
    """Save normalized Codex OAuth token metadata to a Codex typed env file."""
    path = Path(target_path)
    values = {
        key: value
        for key, value in (dotenv_values(path).items() if path.exists() else [])
        if value is not None
    }
    values.update(
        {
            "CODEX_ACCESS_TOKEN": str(token_data.get("access_token") or ""),
            "CODEX_REFRESH_TOKEN": str(token_data.get("refresh_token") or ""),
            "CODEX_ACCESS_TOKEN_EXPIRES_AT": str(
                token_data.get("access_token_expires_at") or ""
            ),
            "CODEX_OAUTH_BASE_URL": oauth_base_url,
        }
    )

    CodexConfig.CODEX_ACCESS_TOKEN.value = values["CODEX_ACCESS_TOKEN"]
    CodexConfig.CODEX_REFRESH_TOKEN.value = values["CODEX_REFRESH_TOKEN"]
    CodexConfig.CODEX_ACCESS_TOKEN_EXPIRES_AT.value = values[
        "CODEX_ACCESS_TOKEN_EXPIRES_AT"
    ]
    CodexConfig.CODEX_OAUTH_BASE_URL.value = oauth_base_url

    lines = [f"# Description: Env file for {CodexConfig._title}.", ""]
    written: set[str] = set()
    for field in CodexConfig.get_fields().values():
        if field.env_key not in values:
            continue
        if field.desc:
            lines.append(f"# {field.desc}")
        lines.append(f"{field.env_key}={json.dumps(str(values[field.env_key]))}")
        lines.append("")
        written.add(field.env_key)
    for key, value in values.items():
        if key in written:
            continue
        lines.append(f"{key}={json.dumps(str(value))}")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    path.chmod(0o600)
    return path


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

    Returns normalized token metadata suitable for CodexConfig storage. The
    refresh token is opaque; the authoritative expiry comes from the OAuth
    token endpoint's ``expires_in`` response.
    """
    refresh_token = (refresh_token or "").strip()
    if not refresh_token:
        raise ValueError("refresh_token is required")

    refreshed_at = now or datetime.now(timezone.utc)
    resolved_base_url = (
        base_url
        or (CodexConfig.CODEX_OAUTH_BASE_URL.value or "").strip()
        or CODEX_OAUTH_BASE_URL
    )
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
