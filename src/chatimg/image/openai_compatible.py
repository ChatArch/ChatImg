import base64
import os
from pathlib import Path
from typing import Any, Optional

import requests
from chatimg.config import OpenAIConfig

from .base import ImageGenerator


def _strip_env_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _load_active_openai_env() -> dict[str, str]:
    chatarch_home = Path(os.environ.get("CHATARCH_HOME") or Path.home() / ".chatarch")
    active_path = chatarch_home / "envs" / "OpenAI" / ".env"
    if not active_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in active_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in {"OPENAI_API_KEY", "OPENAI_API_BASE", "OPENAI_IMAGE_MODEL"}:
            values[key] = _strip_env_quotes(value)
    return values


def _normalize_image_model(model: str | None) -> tuple[str, str | None]:
    active_env = _load_active_openai_env()
    value = (
        model
        or active_env.get("OPENAI_IMAGE_MODEL")
        or OpenAIConfig.OPENAI_IMAGE_MODEL.value
        or os.environ.get("OPENAI_IMAGE_MODEL")
        or "gpt-image-2"
    ).strip()
    for suffix in ("-low", "-medium", "-high"):
        if value.endswith(suffix):
            return value[: -len(suffix)], suffix.removeprefix("-")
    return value, None


class OpenAICompatibleImageGenerator(ImageGenerator):
    """OpenAI-compatible Images API generator using ChatEnv OpenAI config."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        image_model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        active_env = _load_active_openai_env()
        self.api_key = (
            api_key
            or OpenAIConfig.OPENAI_API_KEY.value
            or active_env.get("OPENAI_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
        )
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")

        self.api_base = (
            api_base
            or OpenAIConfig.OPENAI_API_BASE.value
            or active_env.get("OPENAI_API_BASE")
            or os.environ.get("OPENAI_API_BASE")
            or ""
        ).rstrip("/")
        if not self.api_base:
            raise ValueError("OPENAI_API_BASE not set")

        self.image_model, self.default_quality = _normalize_image_model(image_model)
        self.timeout_seconds = float(timeout_seconds or 300)

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        size: str = "1024x1024",
        quality: Optional[str] = None,
        background: Optional[str] = None,
        **kwargs: Any,
    ) -> bytes:
        image_model, model_quality = _normalize_image_model(model or self.image_model)
        payload = {
            "model": image_model,
            "prompt": prompt,
            "size": size,
            "quality": quality or model_quality or self.default_quality or "medium",
            "n": 1,
            **kwargs,
        }
        if background:
            payload["background"] = background
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            f"{self.api_base}/images/generations",
            json=payload,
            headers=headers,
            timeout=self.timeout_seconds,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Images API error ({response.status_code}): {response.text}")

        data = response.json()
        item = (data.get("data") or [{}])[0]
        if item.get("b64_json"):
            return base64.b64decode(item["b64_json"])
        if item.get("url"):
            url_response = requests.get(item["url"], timeout=self.timeout_seconds)
            if url_response.status_code != 200:
                raise RuntimeError(f"Image download error ({url_response.status_code}): {url_response.text}")
            return url_response.content
        raise RuntimeError(f"Unknown Images API response format: {data}")

    def get_models(self) -> list[dict]:
        return [
            {"id": "gpt-image-2-low"},
            {"id": "gpt-image-2-medium"},
            {"id": "gpt-image-2-high"},
        ]
