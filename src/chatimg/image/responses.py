"""Complete-request Responses SSE validation shared by key and OAuth paths."""
import base64
import binascii
import json
from typing import Any, Iterable, Iterator


def iter_sse_json_events(lines: Iterable[bytes | str]) -> Iterator[dict[str, Any]]:
    """Yield JSON objects from complete SSE frames in an iterable of lines."""

    data_lines: list[str] = []
    event_name: str | None = None

    def decode_frame() -> dict[str, Any] | None:
        nonlocal event_name
        frame_type, event_name = event_name, None
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
        if frame_type and "type" not in event:
            event["type"] = frame_type
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
        elif field == "event":
            event_name = value
    if data_lines:
        raise RuntimeError("Responses API stream ended with an unterminated SSE frame")


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


def final_image_b64(events: Iterable[dict[str, Any]]) -> str:
    finals: dict[str, str] = {}
    completed = False
    for event in events:
        event_type = event.get("type")
        if not isinstance(event_type, str):
            raise RuntimeError("Responses API returned malformed SSE payload")
        if event_type == "error":
            error = event.get("error")
            if not isinstance(error, dict):
                raise RuntimeError("Responses API returned malformed error payload")
            raise RuntimeError("Responses API returned an error event")
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
                raise RuntimeError("Responses API terminal status is not completed")
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
    return next(iter(finals.values()))
