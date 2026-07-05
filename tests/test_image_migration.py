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

    from chatenv.configs import OpenAIConfig
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
    assert captured["headers"]["Authorization"] == "Bearer crs-key"
    assert captured["timeout"] == 123


def test_openai_compatible_generator_does_not_fallback_to_oauth_token(monkeypatch, tmp_path):
    from chatenv.configs import OpenAIConfig
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
    from chatenv.configs import OpenAIConfig
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
    from chatenv.configs import OpenAIConfig
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
    from chatenv.configs import OpenAIConfig
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


def test_codex_uses_codex_env_aliases(monkeypatch):
    from chatimg.config import OpenAIConfig
    from chatimg.image.codex import CodexImageGenerator

    original = {
        "OPENAI_ACCESS_TOKEN": OpenAIConfig.OPENAI_ACCESS_TOKEN.value,
        "OPENAI_CODEX_ACCESS_TOKEN": OpenAIConfig.OPENAI_CODEX_ACCESS_TOKEN.value,
        "OPENAI_IMAGE_ASPECT_RATIO": OpenAIConfig.OPENAI_IMAGE_ASPECT_RATIO.value,
        "OPENAI_CODEX_HOST_MODEL": OpenAIConfig.OPENAI_CODEX_HOST_MODEL.value,
        "OPENAI_CODEX_BASE_URL": OpenAIConfig.OPENAI_CODEX_BASE_URL.value,
        "OPENAI_CODEX_TIMEOUT": OpenAIConfig.OPENAI_CODEX_TIMEOUT.value,
    }
    try:
        OpenAIConfig.OPENAI_ACCESS_TOKEN.value = ""
        OpenAIConfig.OPENAI_CODEX_ACCESS_TOKEN.value = "not-a-jwt"
        OpenAIConfig.OPENAI_IMAGE_ASPECT_RATIO.value = "portrait"
        OpenAIConfig.OPENAI_CODEX_HOST_MODEL.value = "gpt-5.4"
        OpenAIConfig.OPENAI_CODEX_BASE_URL.value = "https://chatgpt.com/backend-api/codex"
        OpenAIConfig.OPENAI_CODEX_TIMEOUT.value = "123"
        generator = CodexImageGenerator(image_model="gpt-image-2-low")
        assert generator.resolve_access_token() == "not-a-jwt"
        assert generator.aspect_ratio == "portrait"
        assert generator.host_model == "gpt-5.4"
        assert generator.base_url == "https://chatgpt.com/backend-api/codex"
        assert generator.timeout_seconds == 123.0
    finally:
        for key, value in original.items():
            getattr(OpenAIConfig, key).value = value


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


def test_chatenv_config_contains_image_provider_fields():
    from chatimg.config import ChatImgConfig

    expected = {
        "DASHSCOPE_API_KEY",
        "HUGGINGFACE_HUB_TOKEN",
        "LIBLIB_ACCESS_KEY",
        "LIBLIB_SECRET_KEY",
        "LIBLIB_MODEL_ID",
        "POLLINATIONS_API_KEY",
        "POLLINATIONS_MODEL_ID",
        "SILICONFLOW_API_KEY",
        "SILICONFLOW_MODEL_ID",
        "OPENAI_ACCESS_TOKEN",
        "OPENAI_CODEX_ACCESS_TOKEN",
        "OPENAI_REFRESH_TOKEN",
        "OPENAI_CODEX_AUTH_JSON",
        "OPENAI_OAUTH_BASE_URL",
        "OPENAI_ACCESS_TOKEN_EXPIRES_AT",
        "OPENAI_IMAGE_MODEL",
        "OPENAI_IMAGE_ASPECT_RATIO",
        "OPENAI_CODEX_HOST_MODEL",
        "OPENAI_CODEX_BASE_URL",
        "OPENAI_CODEX_TIMEOUT",
    }
    actual = {
        value.env_key
        for value in vars(ChatImgConfig).values()
        if hasattr(value, "env_key")
    }
    assert expected <= actual
