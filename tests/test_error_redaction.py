"""Upstream error data must not become CLI credential disclosure."""
from types import SimpleNamespace

import pytest
from chatenv import EnvStore
from chatenv.configs import OpenAIConfig

from chatimg.image import openai_compatible
from chatimg.image.responses import final_image_b64

CANARY = "fixture-upstream-credential-canary"


def test_codex_http_error_does_not_echo_body(monkeypatch):
    import httpx
    from chatimg.image.codex import CodexImageGenerator

    real_client = httpx.Client
    calls = []

    def respond(request):
        calls.append(str(request.url))
        return httpx.Response(401, text=CANARY)

    monkeypatch.setattr(httpx, "Client", lambda **kwargs: real_client(
        transport=httpx.MockTransport(respond), **kwargs
    ))
    client = CodexImageGenerator.__new__(CodexImageGenerator)
    client.base_url = "https://relay.example.invalid/backend-api/codex"
    with pytest.raises(RuntimeError) as error:
        client.request_image_b64(
            "fixture-access-token", prompt="fixture", host_model="fixture-model",
            image_model="gpt-image-2-low", aspect_ratio="square", timeout_seconds=1,
        )
    assert "401" in str(error.value)
    assert CANARY not in str(error.value)
    assert calls == [client.base_url + "/responses"]


@pytest.fixture
def generator(tmp_path, monkeypatch):
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))
    EnvStore(tmp_path / "envs").save_profile(OpenAIConfig, "work", {
        "OPENAI_API_KEY": "fixture-caller-key",
        "OPENAI_API_BASE": "https://relay.example.invalid/openai/v1",
    })
    return openai_compatible.OpenAICompatibleImageGenerator(profile="work")


@pytest.mark.parametrize("mode", ["images", "responses"])
def test_http_error_does_not_echo_body(generator, monkeypatch, mode):
    calls = []
    response = SimpleNamespace(status_code=401, text=CANARY, close=lambda: None)
    monkeypatch.setattr(openai_compatible.http, "post", lambda *a, **k: calls.append(a[0]) or response)
    generator.api_mode = mode
    with pytest.raises(RuntimeError) as error:
        generator.generate("fixture", quality="low")
    assert "401" in str(error.value)
    assert CANARY not in str(error.value)
    assert len(calls) == 1
    assert calls[0].startswith(generator.api_base)


def test_unknown_images_response_is_not_dumped(generator, monkeypatch):
    response = SimpleNamespace(status_code=200, json=lambda: {"unexpected": CANARY})
    monkeypatch.setattr(openai_compatible.http, "post", lambda *a, **k: response)
    with pytest.raises(RuntimeError) as error:
        generator.generate("fixture")
    assert CANARY not in str(error.value)


@pytest.mark.parametrize("event", [
    {"type": "error", "error": {"message": CANARY}},
    {"type": "response.completed", "response": {"status": CANARY}},
])
def test_stream_errors_do_not_echo_untrusted_text(event):
    with pytest.raises(RuntimeError) as error:
        final_image_b64([event])
    assert CANARY not in str(error.value)
