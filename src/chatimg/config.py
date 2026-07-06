"""Typed environment configuration for ChatImg."""

from chatenv import BaseEnvConfig, EnvField
from chatenv.configs import OpenAIConfig


class ChatImgConfig(BaseEnvConfig):
    """ChatImg ChatEnv configuration for image generation providers."""

    _title = "ChatImg Configuration"
    _aliases = ["chatimg", "image"]
    _storage_dir = "ChatImg"

    DASHSCOPE_API_KEY = EnvField(
        "DASHSCOPE_API_KEY",
        desc="Aliyun DashScope API key for Tongyi Wanxiang.",
        is_sensitive=True,
    )
    HUGGINGFACE_HUB_TOKEN = EnvField(
        "HUGGINGFACE_HUB_TOKEN",
        desc="Hugging Face User Access Token.",
        is_sensitive=True,
    )
    LIBLIB_MODEL_ID = EnvField(
        "LIBLIB_MODEL_ID",
        desc="Default LiblibAI model ID.",
    )
    LIBLIB_ACCESS_KEY = EnvField(
        "LIBLIB_ACCESS_KEY",
        desc="LiblibAI access key.",
        is_sensitive=True,
    )
    LIBLIB_SECRET_KEY = EnvField(
        "LIBLIB_SECRET_KEY",
        desc="LiblibAI secret key.",
        is_sensitive=True,
    )
    POLLINATIONS_API_KEY = EnvField(
        "POLLINATIONS_API_KEY",
        desc="Pollinations API key from enter.pollinations.ai.",
        is_sensitive=True,
    )
    POLLINATIONS_MODEL_ID = EnvField(
        "POLLINATIONS_MODEL_ID",
        default="flux",
        desc="Default Pollinations image model ID.",
    )
    SILICONFLOW_API_KEY = EnvField(
        "SILICONFLOW_API_KEY",
        desc="SiliconFlow API key.",
        is_sensitive=True,
    )
    SILICONFLOW_MODEL_ID = EnvField(
        "SILICONFLOW_MODEL_ID",
        default="black-forest-labs/FLUX.1-schnell",
        desc="Default SiliconFlow image model ID.",
    )

    @classmethod
    def test(cls) -> None:
        """Validate schema registration without external side effects."""

        print(f"Testing {cls._title}...")
        print("Schema loaded; provider network checks are command-specific.")


class CodexConfig(BaseEnvConfig):
    """Codex OAuth image bridge configuration owned by ChatImg."""

    _title = "Codex Configuration"
    _aliases = ["codex"]
    _storage_dir = "Codex"

    CODEX_ACCESS_TOKEN = EnvField(
        "CODEX_ACCESS_TOKEN",
        desc="Codex OAuth access token for the Codex image bridge.",
        is_sensitive=True,
    )
    CODEX_REFRESH_TOKEN = EnvField(
        "CODEX_REFRESH_TOKEN",
        desc="Codex OAuth refresh token for the Codex image bridge.",
        is_sensitive=True,
    )
    CODEX_ACCESS_TOKEN_EXPIRES_AT = EnvField(
        "CODEX_ACCESS_TOKEN_EXPIRES_AT",
        desc="UTC ISO timestamp for CODEX_ACCESS_TOKEN expiry.",
    )
    CODEX_OAUTH_BASE_URL = EnvField(
        "CODEX_OAUTH_BASE_URL",
        default="https://auth.openai.com",
        desc="Codex OAuth auth server base URL.",
    )
    CODEX_API_BASE = EnvField(
        "CODEX_API_BASE",
        default="https://chatgpt.com/backend-api/codex",
        desc="Codex Responses API base URL.",
    )
    CODEX_HOST_MODEL = EnvField(
        "CODEX_HOST_MODEL",
        default="gpt-5.4",
        desc="Codex host model used to invoke the image_generation tool.",
    )
    CODEX_IMAGE_MODEL = EnvField(
        "CODEX_IMAGE_MODEL",
        default="gpt-image-2-medium",
        desc="Default Codex image model preset.",
    )

    @classmethod
    def test(cls) -> None:
        """Validate schema registration without external side effects."""

        print(f"Testing {cls._title}...")
        print("Schema loaded; token checks are command-specific.")


# Backward-compatible aliases for code migrated from ChatTool provider modules.
ChatimgConfig = ChatImgConfig
TongyiConfig = ChatImgConfig
HuggingFaceConfig = ChatImgConfig
LiblibConfig = ChatImgConfig
PollinationsConfig = ChatImgConfig
SiliconFlowConfig = ChatImgConfig

__all__ = [
    "ChatImgConfig",
    "ChatimgConfig",
    "CodexConfig",
    "TongyiConfig",
    "HuggingFaceConfig",
    "LiblibConfig",
    "PollinationsConfig",
    "SiliconFlowConfig",
    "OpenAIConfig",
]
