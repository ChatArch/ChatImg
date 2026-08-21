# CLI Tree

ChatImg `0.1.6` uses ChatStyle's shared Click tree runtime to render the real registered command surface. The module entry point and console script both use the public CLI name `chatimg` as the canonical root.

## Default tree

`chatimg --tree` includes parameter signatures by default:

```text
chatimg
├── --help  # Show this message and exit.
├── --version  # Show the version and exit.
├── --tree  # Print the registered CLI tree and exit.
├── --tree-brief  # Print the registered CLI tree without parameter signatures and exit.
├── codex  # ChatGPT/Codex OAuth image tools.
│   ├── auth-refresh [--profile PROFILE]  # Refresh OpenAI OAuth tokens and persist the runtime token store.
│   ├── auth-status [--profile PROFILE]  # Show safe OpenAI OAuth profile status without token values.
│   ├── generate [PROMPT] [--aspect-ratio ASPECT-RATIO] [--image-model IMAGE-MODEL] [--host-model HOST-MODEL] [--base-url BASE-URL] [--profile PROFILE] [--timeout TIMEOUT] [--output OUTPUT] [--interactive]  # Generate an image using the ChatGPT/Codex OAuth image bridge.
│   └── list-models [--profile PROFILE]  # List built-in Codex image model presets.
├── huggingface  # Hugging Face tools.
│   └── generate [PROMPT] [--output OUTPUT] [--interactive]  # Generate an image using Hugging Face.
├── liblib  # LiblibAI tools.
│   ├── generate [PROMPT] [--model-id MODEL-ID] [--output OUTPUT] [--interactive]  # Generate an image using LiblibAI.
│   └── list-models  # List available models for LiblibAI.
├── openai  # OpenAI-compatible Images API tools, including CRS proxy.
│   └── generate [PROMPT] [--model IMAGE-MODEL] [--size SIZE] [--quality QUALITY] [--api-base API-BASE] [--timeout TIMEOUT] [--output OUTPUT] [--interactive]  # Generate an image using OpenAI-compatible Images API.
├── pollinations  # Pollinations.ai tools.
│   ├── generate [PROMPT] [--model MODEL] [--width WIDTH] [--height HEIGHT] [--output OUTPUT] [--interactive]  # Generate an image using Pollinations.ai.
│   └── list-models  # List available image models for Pollinations.ai.
├── siliconflow  # SiliconFlow tools.
│   ├── generate [PROMPT] [--model MODEL] [--size SIZE] [--output OUTPUT] [--interactive]  # Generate an image using SiliconFlow API.
│   └── list-models  # List available image models for SiliconFlow.
└── tongyi  # Tongyi Wanxiang tools.
    └── generate [PROMPT] [--style STYLE] [--size SIZE] [--output OUTPUT] [--interactive]  # Generate an image using Tongyi Wanxiang.
```

## Brief tree

`chatimg --tree-brief` keeps the same command nodes and descriptions while omitting parameter signatures:

```text
chatimg
├── --help  # Show this message and exit.
├── --version  # Show the version and exit.
├── --tree  # Print the registered CLI tree and exit.
├── --tree-brief  # Print the registered CLI tree without parameter signatures and exit.
├── codex  # ChatGPT/Codex OAuth image tools.
│   ├── auth-refresh  # Refresh OpenAI OAuth tokens and persist the runtime token store.
│   ├── auth-status  # Show safe OpenAI OAuth profile status without token values.
│   ├── generate  # Generate an image using the ChatGPT/Codex OAuth image bridge.
│   └── list-models  # List built-in Codex image model presets.
├── huggingface  # Hugging Face tools.
│   └── generate  # Generate an image using Hugging Face.
├── liblib  # LiblibAI tools.
│   ├── generate  # Generate an image using LiblibAI.
│   └── list-models  # List available models for LiblibAI.
├── openai  # OpenAI-compatible Images API tools, including CRS proxy.
│   └── generate  # Generate an image using OpenAI-compatible Images API.
├── pollinations  # Pollinations.ai tools.
│   ├── generate  # Generate an image using Pollinations.ai.
│   └── list-models  # List available image models for Pollinations.ai.
├── siliconflow  # SiliconFlow tools.
│   ├── generate  # Generate an image using SiliconFlow API.
│   └── list-models  # List available image models for SiliconFlow.
└── tongyi  # Tongyi Wanxiang tools.
    └── generate  # Generate an image using Tongyi Wanxiang.
```

## Boundaries

- `hello` is not a ChatImg business interface and must not appear in the public CLI tree.
- `codex` is the ChatGPT/Codex OAuth-backed image bridge, not the external Codex CLI.
- `codex` reads the ChatEnv `OpenAI` profile: runtime token-store `tokens/OpenAI/<profile>.json` wins, and `envs/OpenAI/<profile>.env` is only the seed/fallback.
- `openai` / `crs` use the OpenAI-compatible Images API and `OPENAI_API_KEY`; they do not fall back to OAuth tokens.
