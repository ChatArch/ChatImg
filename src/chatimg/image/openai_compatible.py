import base64
import os
from typing import Any, Optional

import requests
from chatenv.configs import OpenAIConfig

from .base import ImageGenerator


def _normalize_image_model(model: str | None) -> tuple[str, str | None]:
    value = (model or OpenAIConfig.OPENAI_IMAGE_MODEL.value or "gpt-image-2").strip()
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
        self.api_key = api_key or OpenAIConfig.OPENAI_API_KEY.value or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")

        self.api_base = (
            api_base
            or OpenAIConfig.OPENAI_API_BASE.value
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
        output_format: str = "png",
        background: str = "opaque",
        **kwargs: Any,
    ) -> bytes:
        image_model, model_quality = _normalize_image_model(model or self.image_model)
        payload = {
            "model": image_model,
            "prompt": prompt,
            "size": size,
            "quality": quality or model_quality or self.default_quality or "medium",
            "output_format": output_format,
            "background": background,
            "n": 1,
            **kwargs,
        }
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
