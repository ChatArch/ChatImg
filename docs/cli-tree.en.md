# CLI Tree

`chatimg --tree` is generated from the real registered Click command surface. Use it to verify the provider groups and leaf commands currently exposed by ChatImg. This page records the implemented `0.1.5` command shape; when commands are added or removed, update the CLI registration first and then synchronize `--tree`, tests, and docs.

## Top-level command

```text
chatimg # ChatImg image generation tools.
├── --help # Show this message and exit.
├── --version # Show the version and exit.
├── --tree # Print the registered command tree.
├── codex # ChatGPT/Codex OAuth image tools.
├── huggingface # Hugging Face tools.
├── liblib # LiblibAI tools.
├── openai # OpenAI-compatible Images API tools, including CRS proxy.
├── pollinations # Pollinations.ai tools.
├── siliconflow # SiliconFlow tools.
└── tongyi # Tongyi Wanxiang tools.
```

## Provider groups

### `codex`

```text
codex # ChatGPT/Codex OAuth image tools.
├── codex auth-refresh [--profile PROFILE] # Refresh OpenAI OAuth tokens and persist the runtime token store.
├── codex auth-status [--profile PROFILE] # Show safe OpenAI OAuth profile status without token values.
├── codex generate [PROMPT] [--aspect-ratio ASPECT-RATIO] [--image-model IMAGE-MODEL] [--host-model HOST-MODEL] [--base-url BASE-URL] [--profile PROFILE] [--timeout TIMEOUT] [--output OUTPUT] [--interactive] # Generate an image using the ChatGPT/Codex OAuth image bridge.
└── codex list-models [--profile PROFILE] # List built-in Codex image model presets.
```

### `openai`

```text
openai # OpenAI-compatible Images API tools, including CRS proxy.
└── openai generate [PROMPT] [--model IMAGE-MODEL] [--size SIZE] [--quality QUALITY] [--api-base API-BASE] [--timeout TIMEOUT] [--output OUTPUT] [--interactive] # Generate an image using OpenAI-compatible Images API.
```

### Other providers

```text
huggingface # Hugging Face tools.
└── huggingface generate [PROMPT] [--output OUTPUT] [--interactive] # Generate an image using Hugging Face.

liblib # LiblibAI tools.
├── liblib generate [PROMPT] [--model-id MODEL-ID] [--output OUTPUT] [--interactive] # Generate an image using LiblibAI.
└── liblib list-models # List available models for LiblibAI.

pollinations # Pollinations.ai tools.
├── pollinations generate [PROMPT] [--model MODEL] [--width WIDTH] [--height HEIGHT] [--output OUTPUT] [--interactive] # Generate an image using Pollinations.ai.
└── pollinations list-models # List available image models for Pollinations.ai.

siliconflow # SiliconFlow tools.
├── siliconflow generate [PROMPT] [--model MODEL] [--size SIZE] [--output OUTPUT] [--interactive] # Generate an image using SiliconFlow API.
└── siliconflow list-models # List available image models for SiliconFlow.

tongyi # Tongyi Wanxiang tools.
└── tongyi generate [PROMPT] [--style STYLE] [--size SIZE] [--output OUTPUT] [--interactive] # Generate an image using Tongyi Wanxiang.
```

## Boundaries

- `hello` is not a ChatImg business interface and must not appear in the public CLI tree.
- `codex` is the ChatGPT/Codex OAuth-backed image bridge, not the external Codex CLI.
- `codex` reads the ChatEnv `OpenAI` profile: runtime token-store `tokens/OpenAI/<profile>.json` wins, and `envs/OpenAI/<profile>.env` is only the seed/fallback.
- `openai` / `crs` use the OpenAI-compatible Images API and `OPENAI_API_KEY`; they do not fall back to OAuth tokens.
