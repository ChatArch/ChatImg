import base64
import os
from typing import Any, Optional

from chatenv import EnvStore, get_paths
from chatenv.configs import OpenAIConfig

from chatimg import http
from chatimg.config import ChatImgConfig
from chatimg.http import require_base_url

from .base import ImageGenerator
from .responses import _decode_final_image, final_image_b64, iter_sse_json_events

DEFAULT_HOST_MODEL = "gpt-5.5"


def _load_openai_env(profile: str | None = None) -> dict[str, str]:
    store = EnvStore(get_paths().envs_dir)
    if profile is None:
        values = store.load_active(OpenAIConfig)
    else:
        try:
            values = store.load_profile(OpenAIConfig, profile)
        except FileNotFoundError as exc:
            raise ValueError(f"OpenAI profile not found: {profile}") from exc
    return {str(key): str(value) for key, value in values.items() if value is not None}


def _load_chatimg_env() -> dict[str, str]:
    values = EnvStore(get_paths().envs_dir).load_active(ChatImgConfig)
    return {str(key): str(value) for key, value in values.items() if value is not None}


def _normalize_image_model(model: str | None, profile_values: dict[str, str]) -> tuple[str, str | None]:
    value = (model or profile_values.get("OPENAI_IMAGE_MODEL") or "gpt-image-2").strip()
    for suffix in ("-low", "-medium", "-high"):
        if value.endswith(suffix):
            return value[: -len(suffix)], suffix.removeprefix("-")
    return value, None


class OpenAICompatibleImageGenerator(ImageGenerator):
    """OpenAI-compatible API-key generator supporting Images and Responses APIs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        image_model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        api_mode: Optional[str] = None,
        host_model: Optional[str] = None,
        profile: Optional[str] = None,
    ):
        profile_values = _load_openai_env(profile)
        chatimg_values = _load_chatimg_env()
        explicit_profile = profile is not None

        def configured(name: str) -> str | None:
            if explicit_profile:
                return profile_values.get(name)
            return os.environ.get(name, profile_values.get(name))

        self.profile = profile
        self.api_key = api_key if api_key is not None else configured("OPENAI_API_KEY")
        if not self.api_key or not self.api_key.strip():
            raise ValueError(f"OPENAI_API_KEY not set{f' in OpenAI profile {profile}' if profile else ''}")
        self.api_base = require_base_url(
            api_base if api_base is not None else configured("OPENAI_API_BASE"),
            "OPENAI_API_BASE",
        )

        model_values = dict(profile_values)
        if not explicit_profile:
            configured_image = configured("OPENAI_IMAGE_MODEL")
            if configured_image:
                model_values["OPENAI_IMAGE_MODEL"] = configured_image
        self.image_model, self.default_quality = _normalize_image_model(image_model, model_values)
        self.host_model = host_model or configured("OPENAI_API_MODEL") or DEFAULT_HOST_MODEL
        self.api_mode = (
            api_mode
            or os.environ.get("CHATIMG_OPENAI_API_MODE")
            or chatimg_values.get("CHATIMG_OPENAI_API_MODE")
            or "images"
        )
        if self.api_mode not in {"images", "responses"}:
            raise ValueError("api_mode must be 'images' or 'responses'")
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
        image_model, model_quality = _normalize_image_model(model or self.image_model, {})
        resolved_quality = quality or model_quality or self.default_quality or "medium"
        if self.api_mode == "responses":
            return self._generate_responses(
                prompt,
                image_model,
                size,
                resolved_quality,
                background=background,
                options=kwargs,
            )
        payload = {
            "model": image_model,
            "prompt": prompt,
            "size": size,
            "quality": resolved_quality,
            "n": 1,
            **kwargs,
        }
        if background:
            payload["background"] = background
        headers = self._headers()
        response = http.post(
            f"{self.api_base}/images/generations",
            json=payload,
            headers=headers,
            timeout=self.timeout_seconds,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Images API error ({response.status_code})")
        data = response.json()
        item = (data.get("data") or [{}])[0]
        if item.get("b64_json"):
            return base64.b64decode(item["b64_json"])
        if item.get("url"):
            url_response = http.get(item["url"], timeout=self.timeout_seconds)
            if url_response.status_code != 200:
                raise RuntimeError(f"Image download error ({url_response.status_code})")
            return url_response.content
        raise RuntimeError("Unknown Images API response format")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _generate_responses(
        self,
        prompt: str,
        image_model: str,
        size: str,
        quality: str,
        *,
        background: str | None,
        options: dict[str, Any],
    ) -> bytes:
        if quality not in {"low", "medium"}:
            raise ValueError("Responses image quality must be 'low' or 'medium'")
        if size not in {"1024x1024", "1536x1024"}:
            raise ValueError("Responses image size must be '1024x1024' or '1536x1024'")
        if options:
            raise ValueError(f"unsupported Responses options: {', '.join(sorted(options))}")
        image_tool = {
            "type": "image_generation",
            "model": image_model,
            "action": "generate",
            "quality": quality,
            "size": size,
            "partial_images": 1,
        }
        if background:
            image_tool["background"] = background
        payload = {
            "model": self.host_model,
            "stream": True,
            "store": False,
            "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
            "instructions": "Use the image_generation tool to generate the requested image.",
            "tools": [image_tool],
            "tool_choice": {"type": "image_generation"},
        }
        response = http.post(
            f"{self.api_base}/responses",
            json=payload,
            headers=self._headers(),
            timeout=self.timeout_seconds,
            stream=True,
        )
        try:
            if response.status_code != 200:
                raise RuntimeError(f"Responses API error ({response.status_code})")
            return _decode_final_image(final_image_b64(iter_sse_json_events(response.iter_lines())))
        finally:
            response.close()

    def get_models(self) -> list[dict]:
        return [{"id": "gpt-image-2-low"}, {"id": "gpt-image-2-medium"}, {"id": "gpt-image-2-high"}]
