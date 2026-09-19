"""Offline transport contracts: only loopback fixtures, never a real image API."""
import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest
import requests
from chatenv import EnvStore, OpenAIConfig, TokenStore, get_paths

from chatimg.codex_oauth import refresh_codex_oauth_token
from chatimg.image import create_generator
from chatimg.image.codex import CodexImageGenerator
from chatimg.image.helpers import download_binary

IMAGE = b"offline-final-image-fixture"
FINAL = {"id": "img_1", "type": "image_generation_call", "status": "completed", "result": base64.b64encode(IMAGE).decode()}
DONE = {"type": "response.completed", "response": {"status": "completed", "output": []}}
ITEM = {"type": "response.output_item.done", "item": FINAL}


def sse(*events):
    return b"".join(b"data: " + json.dumps(event).encode() + b"\n\n" for event in events)


@pytest.fixture
def relay():
    """Bounded, owned fake HTTP server with exact request capture."""
    state = {"calls": [], "status": 200, "events": sse(ITEM, DONE), "download": False, "truncated": False}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            state["calls"].append((self.command, self.path, dict(self.headers), body))
            if self.path.endswith("/oauth/token"):
                payload = json.dumps({"access_token": "fresh-fixture", "refresh_token": "rotated-fixture", "expires_in": 3600}).encode()
            elif self.path.endswith("/responses"):
                payload = state["events"]
            else:
                item = {"url": state["url"] + "/image"} if state["download"] else {"b64_json": FINAL["result"]}
                payload = json.dumps({"data": [item]}).encode()
            self.send_response(state["status"])
            self.send_header("Location", state["url"] + "/forbidden-fallback")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            state["calls"].append((self.command, self.path, dict(self.headers), b""))
            self.send_response(state.get("download_status", 200))
            self.send_header("Location", state["url"] + "/forbidden-download")
            self.send_header("Content-Length", str(len(IMAGE) + (5 if state["truncated"] else 0)))
            self.end_headers()
            self.wfile.write(IMAGE)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    state["url"] = f"http://127.0.0.1:{server.server_port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        assert not thread.is_alive()


@pytest.fixture(params=["environment", "system"])
def poisoned_proxies(request, monkeypatch):
    names = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")
    for name in names:
        monkeypatch.delenv(name, raising=False)
    for name in ("NO_PROXY", "no_proxy"):
        monkeypatch.setenv(name, "")
    if request.param == "environment":
        for name in names:
            monkeypatch.setenv(name, "invalid-proxy-scheme://127.0.0.1:1")
    else:
        # Requests and HTTPX import the stdlib system-proxy discovery function.
        monkeypatch.setattr(requests.utils, "getproxies", lambda: {"all": "http://127.0.0.1:1"})
        monkeypatch.setattr(httpx._utils, "getproxies", lambda: {"all": "http://127.0.0.1:1"})


def save_profile(relay, name="work", **overrides):
    values = {
        "OPENAI_API_KEY": "fixture-api-key",
        "OPENAI_API_BASE": relay["url"] + "/nested/relay/openai/v1",
        "OPENAI_API_MODEL": "fixture-carrier",
        "CHATGPT_BACKEND_BASE_URL": relay["url"] + "/nested/backend-api",
        "OPENAI_OAUTH_BASE_URL": relay["url"] + "/nested/auth",
        **overrides,
    }
    EnvStore(get_paths().envs_dir).save_profile(OpenAIConfig, name, values)


@pytest.mark.parametrize("provider", ["openai", "crs"])
@pytest.mark.parametrize("mode", ["images", "responses"])
def test_key_only_named_profile_connects_directly_to_original_base(relay, poisoned_proxies, monkeypatch, provider, mode):
    save_profile(relay)
    monkeypatch.setenv("OPENAI_API_BASE", "https://must-not-call.invalid/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "wrong-process-key")
    monkeypatch.setenv("OPENAI_ACCESS_TOKEN", "wrong-oauth-token")
    monkeypatch.setattr(TokenStore, "read", lambda *_a, **_k: pytest.fail("API-key route read OAuth token store"))
    monkeypatch.setattr(CodexImageGenerator, "resolve_access_token", lambda *_a: pytest.fail("API-key route resolved OAuth"))
    generator = create_generator(provider, profile="work", api_mode=mode, timeout_seconds=2)
    assert generator.generate("offline fixture") == IMAGE
    assert len(relay["calls"]) == 1
    method, path, headers, _body = relay["calls"][0]
    assert method == "POST"
    assert path == "/nested/relay/openai/v1/" + ("responses" if mode == "responses" else "images/generations")
    assert headers["Authorization"] == "Bearer fixture-api-key"


@pytest.mark.parametrize("via_provider", [False, True])
def test_image_url_download_is_direct_without_credential_inheritance(relay, poisoned_proxies, tmp_path, monkeypatch, via_provider):
    netrc = tmp_path / "test.netrc"
    netrc.write_text("machine 127.0.0.1 login unrelated password unrelated\n")
    monkeypatch.setenv("NETRC", str(netrc))
    if via_provider:
        relay["download"] = True
        save_profile(relay)
        assert create_generator("openai", profile="work", api_mode="images").generate("fixture") == IMAGE
    else:
        target = tmp_path / "download.bin"
        assert download_binary(relay["url"] + "/image", target).read_bytes() == IMAGE
    download = relay["calls"][-1]
    assert download[:2] == ("GET", "/image")
    assert "Authorization" not in download[2]
    if via_provider:
        assert relay["calls"][0][2]["Authorization"] == "Bearer fixture-api-key"


def test_netrc_never_replaces_api_key(relay, tmp_path, monkeypatch):
    netrc = tmp_path / "test.netrc"
    netrc.write_text("machine 127.0.0.1 login unrelated password unrelated\n")
    monkeypatch.setenv("NETRC", str(netrc))
    monkeypatch.setenv("NO_PROXY", "*")
    save_profile(relay)
    create_generator("openai", profile="work", api_mode="images").generate("fixture")
    assert relay["calls"][0][2]["Authorization"] == "Bearer fixture-api-key"


@pytest.mark.parametrize("mode", ["images", "responses"])
@pytest.mark.parametrize("status", [302, 307, 401, 502])
def test_no_redirect_protocol_or_credential_retry(relay, monkeypatch, mode, status):
    monkeypatch.setenv("NO_PROXY", "*")
    save_profile(relay)
    relay["status"] = status
    with pytest.raises(RuntimeError):
        create_generator("openai", profile="work", api_mode=mode).generate("fixture")
    assert len(relay["calls"]) == 1


@pytest.mark.parametrize("option,value", [("api_base", ""), ("api_base", "relay.invalid/v1"), ("api_base", "https://relay.invalid/v1?token=fixture"), ("api_base", "https://user:pass@relay.invalid/v1"), ("api_key", "")])
def test_explicit_invalid_settings_fail_without_falling_back(relay, option, value):
    save_profile(relay)
    with pytest.raises(ValueError):
        create_generator("openai", profile="work", **{option: value})
    assert not relay["calls"]


def test_profile_without_base_does_not_use_process_or_official_default(monkeypatch):
    EnvStore(get_paths().envs_dir).save_profile(OpenAIConfig, "key-only", {"OPENAI_API_KEY": "fixture"})
    monkeypatch.setenv("OPENAI_API_BASE", "https://other.invalid/v1")
    with pytest.raises(ValueError, match="OPENAI_API_BASE"):
        create_generator("openai", profile="key-only")


def test_codex_requests_and_existing_oauth_refresh_are_direct(relay, poisoned_proxies):
    save_profile(relay)
    generator = CodexImageGenerator(profile="work", access_token="fixture-oauth", timeout_seconds=2)
    assert generator.generate("fixture") == IMAGE
    result = refresh_codex_oauth_token("fixture-refresh", base_url=generator.oauth_base_url, timeout_seconds=2)
    assert result["access_token"] == "fresh-fixture"
    assert [c[1] for c in relay["calls"]] == ["/nested/backend-api/codex/responses", "/nested/auth/oauth/token"]
    assert relay["calls"][0][2]["Authorization"] == "Bearer fixture-oauth"


@pytest.mark.parametrize("target", ["generation", "refresh"])
def test_codex_missing_endpoint_fails_closed(monkeypatch, target):
    calls = []
    monkeypatch.setattr(httpx.Client, "send", lambda *_a, **_k: calls.append(1) or pytest.fail("unconfigured endpoint reached network"))
    with pytest.raises(ValueError, match="BASE_URL|base_url"):
        if target == "generation":
            CodexImageGenerator(access_token="fixture-oauth").generate("fixture")
        else:
            refresh_codex_oauth_token("fixture-refresh")
    assert not calls


@pytest.mark.parametrize("provider", ["openai", "codex"])
@pytest.mark.parametrize("events", [
    sse(ITEM),
    sse(ITEM, {"type": "response.failed"}),
    sse(ITEM, DONE, {"type": "response.incomplete"}),
    sse(ITEM, DONE, {"type": "error", "error": {"message": "late failure"}}),
    sse({"type": "response.output_image_generation_call.partial_image", "partial_image_b64": FINAL["result"]}, DONE),
    sse(ITEM, DONE).rstrip(b"\n"),
])
def test_sse_never_returns_image_from_failed_or_truncated_request(relay, monkeypatch, provider, events):
    monkeypatch.setenv("NO_PROXY", "*")
    save_profile(relay)
    relay["events"] = events
    kwargs = {"api_mode": "responses"} if provider == "openai" else {"access_token": "fixture-oauth"}
    with pytest.raises(RuntimeError):
        create_generator(provider, profile="work", **kwargs).generate("fixture")
    assert len(relay["calls"]) == 1


@pytest.mark.parametrize("provider", ["openai", "codex"])
def test_completed_output_is_final_not_a_later_preview(relay, monkeypatch, provider):
    monkeypatch.setenv("NO_PROXY", "*")
    save_profile(relay)
    relay["events"] = sse({"type": "response.completed", "response": {"status": "completed", "output": [FINAL]}}, {"type": "response.output_image_generation_call.partial_image", "partial_image_b64": "cHJldmlldw=="})
    kwargs = {"api_mode": "responses"} if provider == "openai" else {"access_token": "fixture-oauth"}
    assert create_generator(provider, profile="work", **kwargs).generate("fixture") == IMAGE


def test_truncated_download_does_not_overwrite_output(relay, tmp_path, monkeypatch):
    monkeypatch.setenv("NO_PROXY", "*")
    relay["truncated"] = True
    target = tmp_path / "image.bin"
    target.write_bytes(b"existing")
    with pytest.raises(requests.exceptions.RequestException):
        download_binary(relay["url"] + "/image", target)
    assert target.read_bytes() == b"existing"


@pytest.mark.parametrize("status", [302, 307, 401, 502])
@pytest.mark.parametrize("target", ["generation", "refresh", "download", "provider-download"])
def test_codex_and_downloads_never_follow_redirects(relay, tmp_path, monkeypatch, target, status):
    monkeypatch.setenv("NO_PROXY", "*")
    save_profile(relay)
    if target in {"download", "provider-download"}:
        relay["download_status"] = status
    else:
        relay["status"] = status
    output = tmp_path / "image.bin"
    with pytest.raises(RuntimeError):
        if target == "generation":
            create_generator("codex", profile="work", access_token="fixture-oauth").generate("fixture")
        elif target == "refresh":
            refresh_codex_oauth_token("fixture-refresh", base_url=relay["url"])
        elif target == "provider-download":
            relay["download"] = True
            create_generator("crs", profile="work", api_mode="images").generate("fixture")
        else:
            download_binary(relay["url"] + "/image", output, headers={"Authorization": "Bearer fixture-download"})
    assert not output.exists()
    assert len(relay["calls"]) == (2 if target == "provider-download" else 1)
    assert all("forbidden" not in call[1] for call in relay["calls"])


@pytest.mark.parametrize("provider", ["openai", "codex"])
def test_responses_preserve_sse_event_field_type(relay, monkeypatch, provider):
    monkeypatch.setenv("NO_PROXY", "*")
    save_profile(relay)
    relay["events"] = b"".join(
        f"event: {event['type']}\ndata: {json.dumps({key: value for key, value in event.items() if key != 'type'})}\n\n".encode()
        for event in (ITEM, DONE)
    )
    kwargs = {"api_mode": "responses"} if provider == "openai" else {"access_token": "fixture-oauth"}
    assert create_generator(provider, profile="work", **kwargs).generate("fixture") == IMAGE


def test_named_codex_refresh_and_generation_keep_profile_and_credentials_isolated(relay, poisoned_proxies, monkeypatch):
    save_profile(relay, OPENAI_REFRESH_TOKEN="wrong-env-seed-refresh")
    env_store = EnvStore(get_paths().envs_dir)
    before_profile = env_store.load_profile(OpenAIConfig, "work")
    env_store.save_active(OpenAIConfig, {
        "OPENAI_ACCESS_TOKEN": "wrong-active-token",
        "CHATGPT_BACKEND_BASE_URL": "https://must-not-call.invalid/backend-api",
        "OPENAI_OAUTH_BASE_URL": "https://must-not-call.invalid/auth",
    })
    token_store = TokenStore()
    token_store.write("OpenAI", "default", values={"access_token": "wrong-default-token"})
    before_default = token_store.read("OpenAI", "default")
    token_store.write("OpenAI", "work", values={"refresh_token": "fixture-refresh"})
    monkeypatch.setenv("OPENAI_ACCESS_TOKEN", "wrong-process-token")
    monkeypatch.setenv("CHATGPT_BACKEND_BASE_URL", "https://must-not-call.invalid/process")
    monkeypatch.setenv("OPENAI_OAUTH_BASE_URL", "https://must-not-call.invalid/process-auth")

    assert create_generator("openai-codex", profile="work", timeout_seconds=2).generate("fixture") == IMAGE

    assert [call[1] for call in relay["calls"]] == ["/nested/auth/oauth/token", "/nested/backend-api/codex/responses"]
    assert b"refresh_token=fixture-refresh" in relay["calls"][0][3]
    assert relay["calls"][1][2]["Authorization"] == "Bearer fresh-fixture"
    saved = token_store.read("OpenAI", "work")
    assert saved["values"]["access_token"] == "fresh-fixture"
    assert saved["values"]["refresh_token"] == "rotated-fixture"
    assert saved["expires_at"]
    assert env_store.load_profile(OpenAIConfig, "work") == before_profile
    assert token_store.read("OpenAI", "default") == before_default
