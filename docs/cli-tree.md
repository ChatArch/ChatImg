# CLI 树

`chatimg --tree` 从实际注册的 Click command surface 生成，用来核对当前包真实暴露的 provider group 和 leaf command。该页面记录 `0.1.5` 的已实现命令形状；新增或移除命令时应先更新 CLI 注册，再由 `--tree`/测试/文档同步。

## 顶层命令

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

## 边界

- `hello` 不属于 ChatImg 业务接口，也不应出现在公开 CLI 树中。
- `codex` 是 ChatGPT/Codex OAuth-backed image bridge，不是外部 Codex CLI。
- `codex` 读取 ChatEnv `OpenAI` profile：runtime token-store `tokens/OpenAI/<profile>.json` 优先，`envs/OpenAI/<profile>.env` 只作为 seed/fallback。
- `openai` / `crs` 走 OpenAI-compatible Images API 和 `OPENAI_API_KEY`，不 fallback 到 OAuth token。
