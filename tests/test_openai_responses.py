import base64
import json

import pytest
from click.testing import CliRunner


def _sse(*events):
    return [f"data: {json.dumps(event)}".encode() for event in events]


class StreamResponse:
    status_code = 200
    text = ""

    def __init__(self, lines):
        self.lines = lines
        self.closed = False

    def iter_lines(self):
        yield from self.lines

    def close(self):
        self.closed = True


def test_responses_request_uses_api_key_and_splits_carrier_from_image_model(monkeypatch):
    from chatimg.image.openai_compatible import OpenAICompatibleImageGenerator

    captured = {}
    raw = base64.b64encode(b"final-image").decode()
    response = StreamResponse(
        _sse(
            {"type": "response.output_image_generation_call.partial_image", "partial_image_b64": base64.b64encode(b"preview").decode()},
            {"type": "response.output_item.done", "item": {"id": "img_1", "type": "image_generation_call", "status": "completed", "result": raw}},
            {"type": "response.completed", "response": {"status": "completed", "output": []}},
        )
    )

    def post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return response

    monkeypatch.setattr("requests.post", post)
    generator = OpenAICompatibleImageGenerator(
        api_key="caller-key",
        api_base="https://crs.example/openai/v1",
        api_mode="responses",
        host_model="gpt-5.5",
        image_model="gpt-image-2-medium",
        timeout_seconds=17,
    )
    assert generator.generate("draw a fox", size="1536x1024") == b"final-image"
    assert captured["url"] == "https://crs.example/openai/v1/responses"
    assert captured["headers"]["Authorization"] == "Bearer caller-key"
    assert captured["stream"] is True
    assert captured["timeout"] == 17
    assert captured["json"] == {
        "model": "gpt-5.5",
        "stream": True,
        "store": False,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": "draw a fox"}]}],
        "instructions": "Use the image_generation tool to generate the requested image.",
        "tools": [{"type": "image_generation", "model": "gpt-image-2", "action": "generate", "quality": "medium", "size": "1536x1024", "partial_images": 1}],
        "tool_choice": {"type": "image_generation"},
    }
    assert response.closed


def test_responses_accepts_final_item_from_completed_output(monkeypatch):
    from chatimg.image.openai_compatible import OpenAICompatibleImageGenerator

    raw = base64.b64encode(b"completed-output").decode()
    response = StreamResponse(_sse({"type": "response.completed", "response": {"status": "completed", "output": [{"id": "img", "type": "image_generation_call", "status": "completed", "result": raw}]}}))
    monkeypatch.setattr("requests.post", lambda *a, **k: response)
    generator = OpenAICompatibleImageGenerator(api_key="key", api_base="https://example/v1", api_mode="responses")
    assert generator.generate("fox") == b"completed-output"
    assert response.closed


@pytest.mark.parametrize(
    "events,match",
    [
        ([{"type": "response.output_image_generation_call.partial_image", "partial_image_b64": "cHJldmlldw=="}, {"type": "response.completed", "response": {"status": "completed", "output": []}}], "final image"),
        ([{"type": "response.failed", "response": {"status": "failed"}}], "failed"),
        ([{"type": "response.incomplete", "response": {"status": "incomplete"}}], "incomplete"),
        ([{"type": "response.completed", "response": {"status": "incomplete", "output": []}}], "incomplete"),
        ([{"type": "response.output_item.done", "item": {"type": "image_generation_call", "status": "completed", "result": "ZmFrZQ=="}}], "terminal"),
        ([{"type": "response.completed", "response": {"status": "completed", "output": [{"type": "image_generation_call", "status": "completed", "result": "%%%"}]}}], "base64"),
    ],
)
def test_responses_rejects_non_success_and_malformed_streams(monkeypatch, events, match):
    from chatimg.image.openai_compatible import OpenAICompatibleImageGenerator

    response = StreamResponse(_sse(*events))
    calls = []
    monkeypatch.setattr("requests.post", lambda *a, **k: calls.append(1) or response)
    generator = OpenAICompatibleImageGenerator(api_key="key", api_base="https://example/v1", api_mode="responses")
    with pytest.raises(RuntimeError, match=match):
        generator.generate("fox")
    assert calls == [1]
    assert response.closed


def test_responses_rejects_late_error_after_final_item(monkeypatch):
    from chatimg.image.openai_compatible import OpenAICompatibleImageGenerator

    response = StreamResponse(_sse(
        {"type": "response.output_item.done", "item": {"type": "image_generation_call", "status": "completed", "result": "ZmFrZQ=="}},
        {"type": "error", "error": {"message": "late failure"}},
        {"type": "response.completed", "response": {"status": "completed", "output": []}},
    ))
    monkeypatch.setattr("requests.post", lambda *a, **k: response)
    generator = OpenAICompatibleImageGenerator(api_key="key", api_base="https://example/v1", api_mode="responses")
    with pytest.raises(RuntimeError, match="late failure"):
        generator.generate("fox")
    assert response.closed


@pytest.mark.parametrize("kwargs,match", [({"quality": "high"}, "quality"), ({"size": "1024x1536"}, "size")])
def test_responses_rejects_unverified_tool_options_without_request(monkeypatch, kwargs, match):
    from chatimg.image.openai_compatible import OpenAICompatibleImageGenerator

    calls = []
    monkeypatch.setattr("requests.post", lambda *a, **k: calls.append(1))
    generator = OpenAICompatibleImageGenerator(api_key="key", api_base="https://example/v1", api_mode="responses")
    with pytest.raises(ValueError, match=match):
        generator.generate("fox", **kwargs)
    assert calls == []


def test_explicit_profile_is_isolated_and_explicit_kwargs_win(monkeypatch, tmp_path):
    from chatimg.config import OpenAIConfig
    from chatimg.image.openai_compatible import OpenAICompatibleImageGenerator

    env_dir = tmp_path / "envs" / "OpenAI"
    env_dir.mkdir(parents=True)
    (env_dir / ".env").write_text("OPENAI_API_KEY=other-key\nOPENAI_API_BASE=https://other/v1\n", encoding="utf-8")
    (env_dir / "work.env").write_text("OPENAI_API_KEY=work-key\nOPENAI_API_BASE=https://work/v1\nOPENAI_API_MODEL=gpt-profile\nOPENAI_IMAGE_MODEL=gpt-image-2-low\n", encoding="utf-8")
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "process-key")
    original_key = OpenAIConfig.OPENAI_API_KEY.value
    OpenAIConfig.OPENAI_API_KEY.value = "configured-other-key"
    try:
        generator = OpenAICompatibleImageGenerator(profile="work", host_model="gpt-explicit", image_model="gpt-image-2-medium")
    finally:
        OpenAIConfig.OPENAI_API_KEY.value = original_key
    assert generator.api_key == "work-key"
    assert generator.api_base == "https://work/v1"
    assert generator.host_model == "gpt-explicit"
    assert generator.image_model == "gpt-image-2"
    assert generator.default_quality == "medium"


def test_missing_explicit_profile_does_not_fall_back(monkeypatch, tmp_path):
    from chatimg.image.openai_compatible import OpenAICompatibleImageGenerator

    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "other-key")
    with pytest.raises((ValueError, FileNotFoundError), match="profile|OPENAI_API_KEY"):
        OpenAICompatibleImageGenerator(profile="missing", api_base="https://example/v1")


def test_typed_mode_setting_and_active_host_model_precedence(monkeypatch, tmp_path):
    from chatimg.config import ChatImgConfig, OpenAIConfig
    from chatimg.image.openai_compatible import OpenAICompatibleImageGenerator

    env_dir = tmp_path / "envs" / "OpenAI"
    env_dir.mkdir(parents=True)
    (env_dir / ".env").write_text(
        "OPENAI_API_KEY=active-key\nOPENAI_API_BASE=https://active/v1\nOPENAI_API_MODEL=gpt-active\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))
    original_mode = ChatImgConfig.CHATIMG_OPENAI_API_MODE.value
    original_host = OpenAIConfig.OPENAI_API_MODEL.value
    try:
        ChatImgConfig.CHATIMG_OPENAI_API_MODE.value = "responses"
        OpenAIConfig.OPENAI_API_MODEL.value = "gpt-config"
        generator = OpenAICompatibleImageGenerator()
    finally:
        ChatImgConfig.CHATIMG_OPENAI_API_MODE.value = original_mode
        OpenAIConfig.OPENAI_API_MODEL.value = original_host
    assert generator.api_mode == "responses"
    assert generator.host_model == "gpt-config"


def test_openai_cli_forwards_responses_profile_and_host_model(monkeypatch, tmp_path):
    from chatimg.cli import main

    captured = {}

    class FakeGenerator:
        image_model = "gpt-image-2"
        host_model = "gpt-5.5"
        api_mode = "responses"

        def generate(self, prompt, **kwargs):
            captured["generate"] = (prompt, kwargs)
            return b"png"

    def factory(provider, **kwargs):
        captured["factory"] = (provider, kwargs)
        return FakeGenerator()

    monkeypatch.setattr("chatimg.image.cli.create_generator", factory)
    output = tmp_path / "out.png"
    result = CliRunner().invoke(main, ["openai", "generate", "fox", "--api-mode", "responses", "--profile", "work", "--host-model", "gpt-5.5", "-o", str(output)])
    assert result.exit_code == 0, result.output
    assert captured["factory"] == ("openai", {"api_base": None, "image_model": None, "timeout_seconds": None, "api_mode": "responses", "profile": "work", "host_model": "gpt-5.5"})
    assert output.read_bytes() == b"png"
