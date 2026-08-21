# CLI 树

ChatImg `0.1.6` 使用 ChatStyle 的共享 Click tree runtime，从实际注册的 command surface 生成树。源码模块入口和 console script 都以公开 CLI 名 `chatimg` 作为 canonical root。

## 默认树

`chatimg --tree` 默认保留参数签名：

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

## 简略树

`chatimg --tree-brief` 保留相同的命令节点和描述，但省略参数签名：

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

## 边界

- `hello` 不属于 ChatImg 业务接口，也不应出现在公开 CLI 树中。
- `codex` 是 ChatGPT/Codex OAuth-backed image bridge，不是外部 Codex CLI。
- `codex` 读取 ChatEnv `OpenAI` profile：runtime token-store `tokens/OpenAI/<profile>.json` 优先，`envs/OpenAI/<profile>.env` 只作为 seed/fallback。
- `openai` / `crs` 走 OpenAI-compatible Images API 和 `OPENAI_API_KEY`，不 fallback 到 OAuth token。
