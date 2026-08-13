from click.testing import CliRunner
import pytest

from chatimg import __version__
from chatimg.cli import main


def test_factory_exposes_chatimg_image_providers():
    from chatimg.image import create_generator
    from chatimg.image.base import ImageGenerator

    providers = {
        "tongyi",
        "huggingface",
        "liblib",
        "pollinations",
        "siliconflow",
        "codex",
        "openai-codex",
        "openai",
        "crs",
    }
    for provider in providers:
        if provider in {"codex", "openai-codex"}:
            generator = create_generator(provider, access_token="not-a-jwt")
        elif provider in {"openai", "crs"}:
            generator = create_generator(provider, api_key="token", api_base="https://example.test/openai/v1")
        elif provider == "pollinations":
            generator = create_generator(provider, api_key="token")
        elif provider == "liblib":
            generator = create_generator(provider, access_key="ak", secret_key="sk")
        else:
            generator = create_generator(provider, api_key="token")
        assert isinstance(generator, ImageGenerator)


def test_openai_compatible_generator_uses_chat_env_config_and_returns_png(monkeypatch):
    import base64

    from chatimg.config import OpenAIConfig
    from chatimg.image.openai_compatible import OpenAICompatibleImageGenerator

    original = {
        "OPENAI_API_BASE": OpenAIConfig.OPENAI_API_BASE.value,
        "OPENAI_API_KEY": OpenAIConfig.OPENAI_API_KEY.value,
        "OPENAI_IMAGE_MODEL": OpenAIConfig.OPENAI_IMAGE_MODEL.value,
    }
    captured = {}

    class Response:
        status_code = 200

        def json(self):
            return {"data": [{"b64_json": base64.b64encode(b"fake-png").decode("utf-8")}]}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["payload"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("requests.post", fake_post)
    try:
        OpenAIConfig.OPENAI_API_BASE.value = "https://crs.example.test/openai/v1"
        OpenAIConfig.OPENAI_API_KEY.value = "crs-key"
        OpenAIConfig.OPENAI_IMAGE_MODEL.value = "gpt-image-2-medium"
        generator = OpenAICompatibleImageGenerator(timeout_seconds=123)
        result = generator.generate("a fox", size="1024x1024")
    finally:
        for key, value in original.items():
            getattr(OpenAIConfig, key).value = value

    assert result == b"fake-png"
    assert captured["url"] == "https://crs.example.test/openai/v1/images/generations"
    assert captured["payload"]["model"] == "gpt-image-2"
    assert captured["payload"]["prompt"] == "a fox"
    assert captured["payload"] == {
        "model": "gpt-image-2",
        "prompt": "a fox",
        "size": "1024x1024",
        "quality": "medium",
        "n": 1,
    }
    assert captured["headers"]["Authorization"] == "Bearer crs-key"
    assert captured["timeout"] == 123


def test_openai_compatible_generator_does_not_fallback_to_oauth_token(monkeypatch, tmp_path):
    from chatimg.config import OpenAIConfig
    from chatimg.image.openai_compatible import OpenAICompatibleImageGenerator

    original = {
        "OPENAI_API_BASE": OpenAIConfig.OPENAI_API_BASE.value,
        "OPENAI_API_KEY": OpenAIConfig.OPENAI_API_KEY.value,
        "OPENAI_ACCESS_TOKEN": OpenAIConfig.OPENAI_ACCESS_TOKEN.value,
        "OPENAI_REFRESH_TOKEN": OpenAIConfig.OPENAI_REFRESH_TOKEN.value,
    }
    try:
        OpenAIConfig.OPENAI_API_BASE.value = "https://crs.example.test/openai/v1"
        OpenAIConfig.OPENAI_API_KEY.value = ""
        OpenAIConfig.OPENAI_ACCESS_TOKEN.value = "oauth-access-token"
        OpenAIConfig.OPENAI_REFRESH_TOKEN.value = "oauth-refresh-token"
        monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_ACCESS_TOKEN", "env-oauth-access-token")

        with pytest.raises(ValueError, match="OPENAI_API_KEY not set"):
            OpenAICompatibleImageGenerator()
    finally:
        for key, value in original.items():
            getattr(OpenAIConfig, key).value = value


def test_openai_compatible_generator_prefers_api_key_over_oauth_token(monkeypatch):
    from chatimg.config import OpenAIConfig
    from chatimg.image.openai_compatible import OpenAICompatibleImageGenerator

    original = {
        "OPENAI_API_BASE": OpenAIConfig.OPENAI_API_BASE.value,
        "OPENAI_API_KEY": OpenAIConfig.OPENAI_API_KEY.value,
        "OPENAI_ACCESS_TOKEN": OpenAIConfig.OPENAI_ACCESS_TOKEN.value,
    }
    captured = {}

    class Response:
        status_code = 200

        def json(self):
            return {"data": [{"b64_json": "ZmFrZS1wbmc="}]}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["headers"] = headers
        return Response()

    monkeypatch.setattr("requests.post", fake_post)
    try:
        OpenAIConfig.OPENAI_API_BASE.value = "https://crs.example.test/openai/v1"
        OpenAIConfig.OPENAI_API_KEY.value = "api-key"
        OpenAIConfig.OPENAI_ACCESS_TOKEN.value = "oauth-access-token"
        monkeypatch.setenv("OPENAI_ACCESS_TOKEN", "env-oauth-access-token")

        OpenAICompatibleImageGenerator().generate("a fox")
    finally:
        for key, value in original.items():
            getattr(OpenAIConfig, key).value = value

    assert captured["headers"]["Authorization"] == "Bearer api-key"


def test_openai_compatible_generator_reads_active_chatenv_openai_env(monkeypatch, tmp_path):
    from chatimg.config import OpenAIConfig
    from chatimg.image.openai_compatible import OpenAICompatibleImageGenerator

    original = {
        "OPENAI_API_BASE": OpenAIConfig.OPENAI_API_BASE.value,
        "OPENAI_API_KEY": OpenAIConfig.OPENAI_API_KEY.value,
        "OPENAI_IMAGE_MODEL": OpenAIConfig.OPENAI_IMAGE_MODEL.value,
    }
    active_dir = tmp_path / "envs" / "OpenAI"
    active_dir.mkdir(parents=True)
    (active_dir / ".env").write_text(
        "OPENAI_API_BASE='https://crs.example.test/openai/v1'\n"
        "OPENAI_API_KEY='active-api-key'\n"
        "OPENAI_ACCESS_TOKEN='must-not-be-read'\n"
        "OPENAI_IMAGE_MODEL='gpt-image-2-medium'\n",
        encoding="utf-8",
    )
    try:
        OpenAIConfig.OPENAI_API_BASE.value = ""
        OpenAIConfig.OPENAI_API_KEY.value = ""
        OpenAIConfig.OPENAI_IMAGE_MODEL.value = ""
        monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        generator = OpenAICompatibleImageGenerator()
    finally:
        for key, value in original.items():
            getattr(OpenAIConfig, key).value = value

    assert generator.api_base == "https://crs.example.test/openai/v1"
    assert generator.api_key == "active-api-key"
    assert generator.image_model == "gpt-image-2"
    assert generator.default_quality == "medium"


def test_openai_compatible_generator_falls_back_to_process_env(monkeypatch, tmp_path):
    from chatimg.config import OpenAIConfig
    from chatimg.image.openai_compatible import OpenAICompatibleImageGenerator

    original = {
        "OPENAI_API_BASE": OpenAIConfig.OPENAI_API_BASE.value,
        "OPENAI_API_KEY": OpenAIConfig.OPENAI_API_KEY.value,
    }
    try:
        OpenAIConfig.OPENAI_API_BASE.value = ""
        OpenAIConfig.OPENAI_API_KEY.value = ""
        monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))
        monkeypatch.setenv("OPENAI_API_BASE", "https://crs.example.test/openai/v1")
        monkeypatch.setenv("OPENAI_API_KEY", "env-crs-key")
        generator = OpenAICompatibleImageGenerator()
    finally:
        for key, value in original.items():
            getattr(OpenAIConfig, key).value = value

    assert generator.api_base == "https://crs.example.test/openai/v1"
    assert generator.api_key == "env-crs-key"

def test_openai_compatible_cli_generate_saves_png(monkeypatch, tmp_path):
    from click.testing import CliRunner
    from chatimg.cli import main

    class FakeGenerator:
        image_model = "gpt-image-2"

        def generate(self, prompt, **kwargs):
            assert prompt == "a fox"
            assert kwargs["size"] == "1024x1024"
            return b"fake-png"

    monkeypatch.setattr("chatimg.image.cli.create_generator", lambda provider, **kwargs: FakeGenerator())
    output = tmp_path / "fox.png"
    result = CliRunner().invoke(
        main,
        ["openai", "generate", "a fox", "--size", "1024x1024", "-o", str(output)],
    )

    assert result.exit_code == 0
    assert output.read_bytes() == b"fake-png"
    assert "Image saved to" in result.output


def test_codex_model_presets_and_payload_shape():
    from chatimg.image.codex import CodexImageGenerator

    generator = CodexImageGenerator(access_token="not-a-jwt")
    model_ids = [item["id"] for item in generator.get_models()]
    assert model_ids == [
        "gpt-image-2-low",
        "gpt-image-2-medium",
        "gpt-image-2-high",
    ]
    payload = generator.build_payload(
        "a fox",
        host_model="gpt-5.4",
        image_model="gpt-image-2-medium",
        aspect_ratio="landscape",
    )
    assert payload["tools"][0]["type"] == "image_generation"
    assert payload["tools"][0]["model"] == "gpt-image-2"
    assert payload["tools"][0]["size"] == "1536x1024"


def test_codex_uses_openai_profile_env_seed_when_token_store_is_empty(monkeypatch, tmp_path):
    from chatimg.image.codex import CodexImageGenerator

    openai_dir = tmp_path / "envs" / "OpenAI"
    openai_dir.mkdir(parents=True)
    (openai_dir / ".env").write_text(
        "OPENAI_ACCESS_TOKEN='not-a-jwt'\n"
        "OPENAI_REFRESH_TOKEN='env-refresh-token'\n"
        "OPENAI_ACCESS_TOKEN_EXPIRES_AT='2030-01-02T03:04:05Z'\n"
        "OPENAI_OAUTH_BASE_URL='https://auth.example.test'\n"
        "CHATGPT_BACKEND_BASE_URL='https://gpt.example.test/backend-api'\n"
        "OPENAI_API_MODEL='gpt-5.4'\n"
        "OPENAI_IMAGE_MODEL='gpt-image-2-low'\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))

    generator = CodexImageGenerator(aspect_ratio="portrait")

    assert generator.resolve_access_token() == "not-a-jwt"
    assert generator.refresh_token == "env-refresh-token"
    assert generator.aspect_ratio == "portrait"
    assert generator.host_model == "gpt-5.4"
    assert generator.base_url == "https://gpt.example.test/backend-api/codex"
    assert generator.image_model == "gpt-image-2-low"
    assert generator.timeout_seconds == 300.0


def test_codex_refresh_only_openai_profile_auto_refreshes_and_persists_token_store(monkeypatch, tmp_path):
    from chatenv import TokenStore
    from chatimg.image.codex import CodexImageGenerator

    openai_dir = tmp_path / "envs" / "OpenAI"
    openai_dir.mkdir(parents=True)
    (openai_dir / ".env").write_text(
        "OPENAI_ACCESS_TOKEN=''\n"
        "OPENAI_REFRESH_TOKEN='old-refresh-token'\n"
        "OPENAI_ACCESS_TOKEN_EXPIRES_AT=''\n"
        "OPENAI_OAUTH_BASE_URL='https://auth.example.test'\n"
        "CHATGPT_BACKEND_BASE_URL='https://codex.example.test/backend-api'\n"
        "OPENAI_API_MODEL='gpt-5.5'\n"
        "OPENAI_IMAGE_MODEL='gpt-image-2-low'\n",
        encoding="utf-8",
    )
    captured = {}

    def fake_refresh(refresh_token, *, base_url=None, **kwargs):
        captured["refresh_token"] = refresh_token
        captured["base_url"] = base_url
        return {
            "access_token": "fresh-access-token",
            "refresh_token": "rotated-refresh-token",
            "access_token_expires_at": "2030-01-02T03:04:05Z",
        }

    monkeypatch.setattr("chatimg.image.codex.refresh_codex_oauth_token", fake_refresh)
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))

    generator = CodexImageGenerator()
    assert generator.access_token is None
    assert generator.refresh_token == "old-refresh-token"
    assert generator.host_model == "gpt-5.5"
    assert generator.resolve_access_token() == "fresh-access-token"

    token_path = TokenStore(home=tmp_path).token_path("OpenAI", "default")
    saved = TokenStore(home=tmp_path).read("OpenAI", "default")
    saved_values = saved["values"]
    assert captured == {
        "refresh_token": "old-refresh-token",
        "base_url": "https://auth.example.test",
    }
    assert saved_values["access_token"] == "fresh-access-token"
    assert saved_values["refresh_token"] == "rotated-refresh-token"
    assert saved_values["access_token_expires_at"] == "2030-01-02T03:04:05Z"
    assert saved["expires_at"] == "2030-01-02T03:04:05Z"
    assert token_path.stat().st_mode & 0o777 == 0o600


def test_codex_auth_status_cli_masks_openai_profile_tokens(monkeypatch, tmp_path):
    from chatenv import TokenStore

    openai_dir = tmp_path / "envs" / "OpenAI"
    openai_dir.mkdir(parents=True)
    (openai_dir / ".env").write_text(
        "OPENAI_OAUTH_BASE_URL='https://auth.example.test'\n"
        "CHATGPT_BACKEND_BASE_URL='https://gpt.example.test/backend-api'\n",
        encoding="utf-8",
    )
    TokenStore(home=tmp_path).write(
        "OpenAI",
        "default",
        values={
            "access_token": "secret-access-token",
            "refresh_token": "secret-refresh-token",
        },
        expires_at="2030-01-02T03:04:05Z",
        source="test",
    )
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))

    result = CliRunner().invoke(main, ["codex", "auth-status"])

    assert result.exit_code == 0
    assert "OpenAI profile: default" in result.output
    assert "Access token: present" in result.output
    assert "Refresh token: present" in result.output
    assert "secret-access-token" not in result.output
    assert "secret-refresh-token" not in result.output


def test_codex_does_not_read_hermes_auth_json_or_legacy_codex_env(monkeypatch, tmp_path):
    from chatimg.image.codex import CodexImageGenerator

    hermes_dir = tmp_path / ".hermes"
    hermes_dir.mkdir()
    (hermes_dir / "auth.json").write_text(
        '{"credential_pool":{"openai-codex":[{"access_token":"not-a-jwt"}]}}',
        encoding="utf-8",
    )
    codex_dir = tmp_path / ".chatarch" / "envs" / "Codex"
    codex_dir.mkdir(parents=True)
    (codex_dir / ".env").write_text(
        "CODEX_ACCESS_TOKEN='legacy-access-token'\n"
        "CODEX_REFRESH_TOKEN='legacy-refresh-token'\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CHATARCH_HOME", raising=False)

    with pytest.raises(ValueError, match="OpenAI OAuth access token"):
        CodexImageGenerator().resolve_access_token()



def test_codex_openai_profile_reads_token_store_before_env_seed(monkeypatch, tmp_path):
    from chatenv import TokenStore
    from chatimg.image.codex import CodexImageGenerator

    openai_dir = tmp_path / "envs" / "OpenAI"
    openai_dir.mkdir(parents=True)
    (openai_dir / "alice.env").write_text(
        "OPENAI_ACCESS_TOKEN='env-access-token'\n"
        "OPENAI_REFRESH_TOKEN='env-refresh-token'\n"
        "OPENAI_ACCESS_TOKEN_EXPIRES_AT='2030-01-02T03:04:05Z'\n"
        "OPENAI_OAUTH_BASE_URL='https://auth.example.test'\n"
        "CHATGPT_BACKEND_BASE_URL='https://gpt.example.test/backend-api'\n"
        "OPENAI_API_MODEL='gpt-5.5'\n"
        "OPENAI_IMAGE_MODEL='gpt-image-2-low'\n",
        encoding="utf-8",
    )
    TokenStore(home=tmp_path).write(
        "OpenAI",
        "alice",
        values={
            "access_token": "store-access-token",
            "refresh_token": "store-refresh-token",
        },
        expires_at="2030-01-02T03:04:05Z",
        source="test",
    )
    codex_dir = tmp_path / "envs" / "Codex"
    codex_dir.mkdir(parents=True)
    (codex_dir / ".env").write_text(
        "CODEX_ACCESS_TOKEN='must-not-be-read'\n"
        "CODEX_API_BASE='https://legacy.example.test'\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))

    generator = CodexImageGenerator(profile="alice")

    assert generator.profile == "alice"
    assert generator.active_env_path == openai_dir / "alice.env"
    assert generator.token_store_path == tmp_path / "tokens" / "OpenAI" / "alice.json"
    assert generator.resolve_access_token() == "store-access-token"
    assert generator.refresh_token == "store-refresh-token"
    assert generator.oauth_base_url == "https://auth.example.test"
    assert generator.base_url == "https://gpt.example.test/backend-api/codex"
    assert generator.host_model == "gpt-5.5"
    assert generator.image_model == "gpt-image-2-low"


def test_codex_token_store_access_token_without_expiry_ignores_env_seed_expiry(
    monkeypatch, tmp_path
):
    from chatenv import TokenStore
    from chatimg.image.codex import CodexImageGenerator

    openai_dir = tmp_path / "envs" / "OpenAI"
    openai_dir.mkdir(parents=True)
    (openai_dir / "alice.env").write_text(
        "OPENAI_ACCESS_TOKEN='env-access-token'\n"
        "OPENAI_ACCESS_TOKEN_EXPIRES_AT='2000-01-02T03:04:05Z'\n"
        "OPENAI_OAUTH_BASE_URL='https://auth.example.test'\n"
        "CHATGPT_BACKEND_BASE_URL='https://gpt.example.test/backend-api'\n",
        encoding="utf-8",
    )
    TokenStore(home=tmp_path).write(
        "OpenAI",
        "alice",
        values={"access_token": "store-access-token"},
        source="test",
    )
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))

    generator = CodexImageGenerator(profile="alice")

    assert generator.access_token == "store-access-token"
    assert generator.access_token_expires_at == ""
    assert generator.resolve_access_token() == "store-access-token"


def test_codex_openai_profile_rejects_path_segments(monkeypatch, tmp_path):
    from chatimg.image.codex import CodexImageGenerator

    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))

    with pytest.raises(ValueError, match="single path segment"):
        CodexImageGenerator(profile="../alice")


def test_codex_openai_profile_refresh_uses_token_store_refresh_and_persists(monkeypatch, tmp_path):
    from chatenv import TokenStore
    from chatimg.image.codex import CodexImageGenerator

    openai_dir = tmp_path / "envs" / "OpenAI"
    openai_dir.mkdir(parents=True)
    (openai_dir / "alice.env").write_text(
        "OPENAI_REFRESH_TOKEN='env-refresh-token'\n"
        "OPENAI_OAUTH_BASE_URL='https://auth.example.test'\n"
        "CHATGPT_BACKEND_BASE_URL='https://gpt.example.test/backend-api'\n",
        encoding="utf-8",
    )
    store = TokenStore(home=tmp_path)
    store.write(
        "OpenAI",
        "alice",
        values={"refresh_token": "store-refresh-token"},
        source="test",
    )
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))
    captured = {}

    def fake_refresh(refresh_token, *, base_url=None, **kwargs):
        captured["refresh_token"] = refresh_token
        captured["base_url"] = base_url
        return {
            "access_token": "fresh-access-token",
            "refresh_token": "rotated-refresh-token",
            "access_token_expires_at": "2030-01-02T03:04:05Z",
        }

    monkeypatch.setattr("chatimg.image.codex.refresh_codex_oauth_token", fake_refresh)

    generator = CodexImageGenerator(profile="alice")
    assert generator.resolve_access_token() == "fresh-access-token"

    saved_values = store.read("OpenAI", "alice")["values"]
    assert captured == {
        "refresh_token": "store-refresh-token",
        "base_url": "https://auth.example.test",
    }
    assert saved_values["access_token"] == "fresh-access-token"
    assert saved_values["refresh_token"] == "rotated-refresh-token"
    assert saved_values["access_token_expires_at"] == "2030-01-02T03:04:05Z"


def test_codex_generate_cli_accepts_openai_profile(monkeypatch, tmp_path):
    from click.testing import CliRunner
    from chatimg.cli import main

    captured = {}

    class FakeGenerator:
        host_model = "gpt-5.5"
        image_model = "gpt-image-2-low"

        def generate(self, prompt):
            captured["prompt"] = prompt
            return b"fake-png"

    def fake_create_generator(provider, **kwargs):
        captured["provider"] = provider
        captured["kwargs"] = kwargs
        return FakeGenerator()

    monkeypatch.setattr("chatimg.image.cli.create_generator", fake_create_generator)
    output = tmp_path / "image.png"

    result = CliRunner().invoke(
        main,
        [
            "codex",
            "generate",
            "a fox",
            "--profile",
            "alice",
            "--image-model",
            "gpt-image-2-low",
            "-o",
            str(output),
        ],
    )

    assert result.exit_code == 0
    assert output.read_bytes() == b"fake-png"
    assert captured["provider"] == "codex"
    assert captured["prompt"] == "a fox"
    assert captured["kwargs"]["profile"] == "alice"
    assert captured["kwargs"]["image_model"] == "gpt-image-2-low"


def test_output_path_helper_uses_generated_directory(tmp_path, monkeypatch):
    from chatimg.image.helpers import resolve_generated_output_path

    monkeypatch.chdir(tmp_path)
    output = resolve_generated_output_path(
        provider="codex",
        model="gpt-image-2-medium",
    )
    assert output.parent == tmp_path / "generated"
    assert output.name.startswith("image_codex_gpt-image-2-medium_")
    assert output.suffix == ".png"


def test_cli_exposes_provider_groups_and_version():
    runner = CliRunner()
    version = runner.invoke(main, ["--version"])
    assert version.exit_code == 0
    assert __version__ in version.output

    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    for command in [
        "codex",
        "huggingface",
        "liblib",
        "openai",
        "pollinations",
        "siliconflow",
        "tongyi",
    ]:
        assert command in result.output


def test_provider_cli_errors_exit_nonzero_without_credentials(monkeypatch):
    runner = CliRunner()
    monkeypatch.delenv("POLLINATIONS_API_KEY", raising=False)
    result = runner.invoke(main, ["pollinations", "list-models"])
    assert result.exit_code != 0
    assert "POLLINATIONS_API_KEY" in result.output


def test_download_binary_uses_timeout_and_creates_parent(monkeypatch, tmp_path):
    from chatimg.image import helpers

    class Response:
        status_code = 200
        content = b"png"

    calls = {}

    def fake_get(url, headers=None, timeout=None):
        calls["url"] = url
        calls["headers"] = headers
        calls["timeout"] = timeout
        return Response()

    monkeypatch.setattr("requests.get", fake_get)
    output = tmp_path / "nested" / "image.png"
    saved = helpers.download_binary("https://example.com/image.png", output)
    assert saved == output
    assert output.read_bytes() == b"png"
    assert calls["timeout"] == 60.0


def test_cli_download_failure_exits_nonzero(monkeypatch):
    from chatimg.config import PollinationsConfig
    from chatimg.image.pollinations import PollinationsImageGenerator

    original_api_key = PollinationsConfig.POLLINATIONS_API_KEY.value
    PollinationsConfig.POLLINATIONS_API_KEY.value = "token"
    monkeypatch.setattr(
        PollinationsImageGenerator,
        "generate",
        lambda self, prompt, **kwargs: ["https://example.com/image.png"],
    )
    monkeypatch.setattr(
        "chatimg.image.cli.download_binary",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("download failed")),
    )

    try:
        result = CliRunner().invoke(
            main,
            ["pollinations", "generate", "a cat", "-o", "out.png"],
        )
    finally:
        PollinationsConfig.POLLINATIONS_API_KEY.value = original_api_key
    assert result.exit_code != 0
    assert "download failed" in result.output


def test_liblib_download_failure_exits_nonzero(monkeypatch):
    from chatimg.config import LiblibConfig
    from chatimg.image.liblib import LiblibImageGenerator

    original_access_key = LiblibConfig.LIBLIB_ACCESS_KEY.value
    original_secret_key = LiblibConfig.LIBLIB_SECRET_KEY.value
    LiblibConfig.LIBLIB_ACCESS_KEY.value = "ak"
    LiblibConfig.LIBLIB_SECRET_KEY.value = "sk"
    monkeypatch.setattr(
        LiblibImageGenerator,
        "generate",
        lambda self, prompt, **kwargs: "https://example.com/image.png",
    )
    monkeypatch.setattr(
        "chatimg.image.cli.download_binary",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("download failed")),
    )

    try:
        result = CliRunner().invoke(
            main,
            ["liblib", "generate", "a dog", "--model-id", "m", "-o", "out.png"],
        )
    finally:
        LiblibConfig.LIBLIB_ACCESS_KEY.value = original_access_key
        LiblibConfig.LIBLIB_SECRET_KEY.value = original_secret_key
    assert result.exit_code != 0
    assert "download failed" in result.output


def test_chatenv_config_contains_image_provider_fields_and_no_codex_env_namespace():
    import chatimg.config as config
    from chatimg.config import ChatImgConfig

    image_expected = {
        "DASHSCOPE_API_KEY",
        "HUGGINGFACE_HUB_TOKEN",
        "LIBLIB_ACCESS_KEY",
        "LIBLIB_SECRET_KEY",
        "LIBLIB_MODEL_ID",
        "POLLINATIONS_API_KEY",
        "POLLINATIONS_MODEL_ID",
        "SILICONFLOW_API_KEY",
        "SILICONFLOW_MODEL_ID",
    }
    image_actual = {
        value.env_key
        for value in vars(ChatImgConfig).values()
        if hasattr(value, "env_key")
    }
    assert image_expected <= image_actual
    assert not any(key.startswith("OPENAI_") or key.startswith("CODEX_") for key in image_actual)
    assert not hasattr(config, "CodexConfig")
