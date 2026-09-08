import base64
import binascii
import json
import os
from typing import Any, Iterable, Iterator, Optional

import requests
from chatenv import EnvStore, get_paths
from chatenv.configs import OpenAIConfig

from chatimg.config import ChatImgConfig

from .base import ImageGenerator

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


def iter_sse_json_events(lines: Iterable[bytes | str]) -> Iterator[dict[str, Any]]:
    """Yield JSON objects from complete SSE frames in an iterable of lines."""

    data_lines: list[str] = []

    def decode_frame() -> dict[str, Any] | None:
        if not data_lines:
            return None
        data = "\n".join(data_lines)
        data_lines.clear()
        if data == "[DONE]":
            return None
        try:
            event = json.loads(data)
        except (TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Responses API returned malformed SSE payload") from exc
        if not isinstance(event, dict):
            raise RuntimeError("Responses API returned malformed SSE payload")
        return event

    for raw_line in lines:
        if not isinstance(raw_line, (bytes, str)):
            raise RuntimeError("Responses API returned malformed SSE payload")
        try:
            line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
        except UnicodeDecodeError as exc:
            raise RuntimeError("Responses API returned malformed SSE payload") from exc
        if line == "":
            event = decode_frame()
            if event is not None:
                yield event
            continue
        if line.startswith(":"):
            continue
        field, separator, value = line.partition(":")
        if separator and value.startswith(" "):
            value = value[1:]
        if field == "data":
            data_lines.append(value)
    if data_lines:
        raise RuntimeError("Responses API stream ended with an unterminated SSE frame")


def _normalize_image_model(model: str | None, profile_values: dict[str, str]) -> tuple[str, str | None]:
    value = (model or profile_values.get("OPENAI_IMAGE_MODEL") or "gpt-image-2").strip()
    for suffix in ("-low", "-medium", "-high"):
        if value.endswith(suffix):
            return value[: -len(suffix)], suffix.removeprefix("-")
    return value, None


def _final_image_item(item: Any) -> tuple[str, str] | None:
    if not isinstance(item, dict):
        return None
    if item.get("type") != "image_generation_call" or item.get("status") != "completed":
        return None
    result = item.get("result")
    if not isinstance(result, str) or not result:
        return None
    return str(item.get("id") or result), result


def _decode_final_image(value: str) -> bytes:
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise RuntimeError("Responses API returned malformed final image base64") from exc


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
            return os.environ.get(name) or profile_values.get(name)

        self.profile = profile
        self.api_key = api_key or configured("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(f"OPENAI_API_KEY not set{f' in OpenAI profile {profile}' if profile else ''}")
        self.api_base = (api_base or configured("OPENAI_API_BASE") or "").rstrip("/")
        if not self.api_base:
            raise ValueError(f"OPENAI_API_BASE not set{f' in OpenAI profile {profile}' if profile else ''}")

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
        response = requests.post(
            f"{self.api_base}/responses",
            json=payload,
            headers=self._headers(),
            timeout=self.timeout_seconds,
            stream=True,
        )
        finals: dict[str, str] = {}
        completed = False
        try:
            if response.status_code != 200:
                raise RuntimeError(f"Responses API error ({response.status_code}): {response.text}")
            for event in iter_sse_json_events(response.iter_lines()):
                event_type = event.get("type")
                if not isinstance(event_type, str):
                    raise RuntimeError("Responses API returned malformed SSE payload")
                if event_type == "error":
                    error = event.get("error")
                    if not isinstance(error, dict):
                        raise RuntimeError("Responses API returned malformed error payload")
                    raise RuntimeError(f"Responses API error: {error.get('message') or error}")
                if event_type in {"response.failed", "response.incomplete"}:
                    raise RuntimeError(f"Responses API {event_type.removeprefix('response.')}")
                if event_type == "response.output_item.done":
                    item = event.get("item")
                    if not isinstance(item, dict):
                        raise RuntimeError("Responses API returned malformed output item")
                    final = _final_image_item(item)
                    if final:
                        finals[final[0]] = final[1]
                if event_type == "response.completed":
                    terminal = event.get("response")
                    if not isinstance(terminal, dict):
                        raise RuntimeError("Responses API returned malformed terminal response")
                    status = terminal.get("status")
                    if status != "completed":
                        raise RuntimeError(f"Responses API terminal status is {status or 'malformed/incomplete'}")
                    output = terminal.get("output", [])
                    if not isinstance(output, list):
                        raise RuntimeError("Responses API returned malformed terminal output")
                    for item in output:
                        if not isinstance(item, dict):
                            raise RuntimeError("Responses API returned malformed output item")
                        final = _final_image_item(item)
                        if final:
                            finals[final[0]] = final[1]
                    completed = True
            if not completed:
                raise RuntimeError("Responses API stream ended without successful terminal completion")
            if not finals:
                raise RuntimeError("Responses API completed without a final image")
            return _decode_final_image(next(iter(finals.values())))
        finally:
            response.close()

    def get_models(self) -> list[dict]:
        return [{"id": "gpt-image-2-low"}, {"id": "gpt-image-2-medium"}, {"id": "gpt-image-2-high"}]
