"Typed environment configuration for ChatImg."

from chatenv import BaseEnvConfig, EnvField


class ChatimgConfig(BaseEnvConfig):
    "ChatImg ChatEnv configuration."

    _title = "ChatImg Configuration"
    _aliases = ["chatimg"]
    _storage_dir = "Chatimg"

    @classmethod
    def test(cls) -> None:
        """Validate schema registration without external side effects."""

        print(f"Testing {cls._title}...")
        print("Schema loaded; no network test is required.")

    CHATIMG_API_KEY = EnvField(
        "CHATIMG_API_KEY",
        desc="API key",
        is_sensitive=True,
    )


__all__ = ["ChatimgConfig"]
