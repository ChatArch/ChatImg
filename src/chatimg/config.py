"""Typed environment configuration for ChatImg."""

from chatenv import BaseEnvConfig, EnvField


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
    OPENAI_ACCESS_TOKEN = EnvField(
        "OPENAI_ACCESS_TOKEN",
        desc="OpenAI/ChatGPT OAuth access token for Codex image generation.",
        is_sensitive=True,
    )
    OPENAI_API_BASE = EnvField(
        "OPENAI_API_BASE",
        desc="OpenAI-compatible API base URL, including /v1.",
    )
    OPENAI_API_KEY = EnvField(
        "OPENAI_API_KEY",
        desc="OpenAI-compatible API key for Images API generation.",
        is_sensitive=True,
    )
    OPENAI_REFRESH_TOKEN = EnvField(
        "OPENAI_REFRESH_TOKEN",
        desc="OpenAI/ChatGPT OAuth refresh token for Codex image generation.",
        is_sensitive=True,
    )
    OPENAI_CODEX_AUTH_JSON = EnvField(
        "OPENAI_CODEX_AUTH_JSON",
        default="~/.hermes/auth.json",
        desc="Hermes auth.json path used as a Codex OAuth token fallback.",
    )
    OPENAI_OAUTH_BASE_URL = EnvField(
        "OPENAI_OAUTH_BASE_URL",
        default="https://auth.openai.com",
        desc="OpenAI OAuth auth server base URL.",
    )
    OPENAI_ACCESS_TOKEN_EXPIRES_AT = EnvField(
        "OPENAI_ACCESS_TOKEN_EXPIRES_AT",
        desc="UTC ISO timestamp for OPENAI_ACCESS_TOKEN expiry.",
    )
    OPENAI_IMAGE_MODEL = EnvField(
        "OPENAI_IMAGE_MODEL",
        default="gpt-image-2-medium",
        desc="Default Codex/OpenAI image model preset.",
    )
    OPENAI_IMAGE_ASPECT_RATIO = EnvField(
        "OPENAI_IMAGE_ASPECT_RATIO",
        default="square",
        desc="Default Codex image aspect ratio.",
    )
    OPENAI_CODEX_HOST_MODEL = EnvField(
        "OPENAI_CODEX_HOST_MODEL",
        default="gpt-5.4",
        desc="Codex host model used to invoke the image_generation tool.",
    )
    OPENAI_CODEX_BASE_URL = EnvField(
        "OPENAI_CODEX_BASE_URL",
        default="https://chatgpt.com/backend-api/codex",
        desc="Codex Responses API base URL.",
    )
    OPENAI_CODEX_TIMEOUT = EnvField(
        "OPENAI_CODEX_TIMEOUT",
        default="300",
        desc="Codex image request timeout in seconds.",
    )

    @classmethod
    def test(cls) -> None:
        """Validate schema registration without external side effects."""

        print(f"Testing {cls._title}...")
        print("Schema loaded; provider network checks are command-specific.")


# Backward-compatible aliases for code migrated from ChatTool provider modules.
ChatimgConfig = ChatImgConfig
TongyiConfig = ChatImgConfig
HuggingFaceConfig = ChatImgConfig
LiblibConfig = ChatImgConfig
PollinationsConfig = ChatImgConfig
SiliconFlowConfig = ChatImgConfig
OpenAIConfig = ChatImgConfig

__all__ = [
    "ChatImgConfig",
    "ChatimgConfig",
    "TongyiConfig",
    "HuggingFaceConfig",
    "LiblibConfig",
    "PollinationsConfig",
    "SiliconFlowConfig",
    "OpenAIConfig",
]
