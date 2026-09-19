"""Direct HTTP transport: no environment/system proxies or ambient credentials."""
from __future__ import annotations

from urllib.parse import urlsplit

import requests


class DirectSession(requests.Session):
    """An owned requests session; never redirect/replay to a different endpoint."""

    def __init__(self):
        super().__init__()
        self.trust_env = False

    def request(self, method, url, **kwargs):
        kwargs["allow_redirects"] = False
        return super().request(method, url, **kwargs)


def request(method: str, url: str, **kwargs) -> requests.Response:
    # Same short-lived-session lifecycle as requests.request(). Streaming
    # callers own and must close the returned response in a finally block.
    with DirectSession() as session:
        return session.request(method, url, **kwargs)


def post(url: str, **kwargs) -> requests.Response:
    return request("POST", url, **kwargs)


def get(url: str, **kwargs) -> requests.Response:
    return request("GET", url, **kwargs)


def require_base_url(value: str | None, name: str) -> str:
    """Reject missing/ambiguous endpoints without guessing an official fallback."""
    try:
        if not isinstance(value, str) or not value:
            raise ValueError
        parts = urlsplit(value)
        _ = parts.port
        if (
            parts.scheme not in {"http", "https"}
            or not parts.hostname
            or parts.username is not None
            or parts.password is not None
            or parts.query
            or parts.fragment
            or "?" in value
            or "#" in value
            or "\\" in value
            or any(c.isspace() or ord(c) < 32 for c in value)
        ):
            raise ValueError
    except ValueError:
        # Do not reflect potentially secret-bearing URLs into logs.
        raise ValueError(f"{name} must be an explicit HTTP(S) base URL without credentials, query or fragment") from None
    return value.rstrip("/")
