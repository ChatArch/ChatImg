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
    "TongyiConfig",
    "HuggingFaceConfig",
    "LiblibConfig",
    "PollinationsConfig",
    "SiliconFlowConfig",
    "OpenAIConfig",
]
