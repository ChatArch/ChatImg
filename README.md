<div align="center">
    <a href="https://pypi.python.org/pypi/ChatImg">
        <img src="https://img.shields.io/pypi/v/ChatImg.svg" alt="PyPI version" />
    </a>
    <a href="https://github.com/ChatArch/ChatImg/actions/workflows/ci.yml">
        <img src="https://github.com/ChatArch/ChatImg/actions/workflows/ci.yml/badge.svg" alt="Tests" />
    </a>
    <a href="https://ChatArch.github.io/ChatImg">
        <img src="https://img.shields.io/badge/docs-mkdocs-blue.svg" alt="Documentation" />
    </a>
</div>

<div align="center">

[English](README.en.md) | [简体中文](README.md)
</div>

# ChatImg

ChatImg 是 ChatArch 的图片生成包，承接原 `chattool image` 中已经解耦的 provider 实现。

当前支持：

- `openai` / `crs`：OpenAI-compatible Images API，走 `OPENAI_API_KEY`，请求 `/v1/images/generations`。
- `codex` / `openai-codex`：ChatGPT/Codex OAuth image bridge，走 `CODEX_ACCESS_TOKEN`，支持 `gpt-image-2-*` preset。
- `pollinations`：Pollinations.ai image URL generation and model listing。
- `siliconflow`：SiliconFlow OpenAI-compatible image generation。
- `huggingface`：Hugging Face Inference image generation。
- `liblib`：LiblibAI signed API generation。
- `tongyi`：通义万相 / DashScope image generation。

## 安装

开发安装：

```bash
pip install -e ".[dev]"
```

通义万相 SDK 可选依赖：

```bash
pip install -e ".[images]"
```

## CLI

```bash
chatimg --help
chatimg --version
chatimg openai generate "a small red apple icon" -o apple.png
chatimg codex list-models
chatimg pollinations list-models
```

生成示例：

```bash
chatimg openai generate "a watercolor fox in the snow" --model gpt-image-2-medium --size 1024x1024 -o fox.png
chatimg codex generate "a watercolor fox in the snow" --aspect-ratio square -o fox-codex.png
chatimg pollinations generate "a cyberpunk cat" --model flux --width 512 --height 512 -o cat.png
chatimg siliconflow generate "a cute dog" --size 1024x1024 -o dog.png
chatimg huggingface generate "A futuristic city at night" -o city.png
chatimg liblib generate "A cute dog" --model-id liblib-sdxl-model -o dog.png
chatimg tongyi generate "一只赛博朋克猫" --size "1024*1024" -o cat.png
```

### OpenAI-compatible / CRS Images API

`openai` provider 对齐 OpenAI 官方 Images API：`POST {OPENAI_API_BASE}/images/generations`。官方 base 是 `https://api.openai.com/v1`，因此完整官方接口是 `https://api.openai.com/v1/images/generations`。CRS 兼容服务可用自己的带 `/v1` base，例如 `https://crs.example/openai/v1`。

常用配置字段：

- `OPENAI_API_BASE`：OpenAI-compatible API base，必须包含 `/v1`。
- `OPENAI_API_KEY`：API key；不会 fallback 到 access token。
- `OPENAI_IMAGE_MODEL`：默认 image preset，例如 `gpt-image-2-medium`，会拆成 `model=gpt-image-2` 与 `quality=medium`。

```bash
chatenv use -t oai apple
chatimg openai generate "a small red apple icon" -o apple.png
```

### Codex / GPT Image2 实测示例

`codex` provider 走 ChatGPT/Codex OAuth-backed Responses API，请求里的 image tool model 是 `gpt-image-2`。它不是外部 Codex CLI。

常用配置字段：

- `CODEX_ACCESS_TOKEN`：Codex OAuth access token。
- `CODEX_REFRESH_TOKEN`：Codex OAuth refresh token，用于刷新 access token。
- `CODEX_ACCESS_TOKEN_EXPIRES_AT`：access token 的 UTC ISO 过期时间。
- `CODEX_OAUTH_BASE_URL`：Codex OAuth auth server base URL，默认 `https://auth.openai.com`。
- `CODEX_API_BASE`：Codex backend base URL，默认 `https://chatgpt.com/backend-api/codex`。
- `CODEX_HOST_MODEL`：承载 `image_generation` tool 的 host model，默认 `gpt-5.4`。
- `CODEX_IMAGE_MODEL`：默认 image preset，默认 `gpt-image-2-medium`。

`codex` provider 不再读取 `~/.hermes/auth.json`，也不再维护 `OPENAI_CODEX_*` 变量。`--timeout` 和 `--aspect-ratio` 是命令级参数，不写入长期 env。

基础验收图：

```bash
chatimg codex generate \
  "A clean minimal ChatImg acceptance test illustration: a friendly robot holding a small picture frame, modern flat design, white background, no text" \
  --image-model gpt-image-2-low \
  --aspect-ratio square \
  -o generated/chatimg-gpt-image2-basic.png \
  --timeout 300
```

快速排序流程图：

```bash
chatimg codex generate \
  "Create a clean landscape technical design flowchart explaining quicksort. Use this exact example array: [6, 3, 8, 5, 1, 10, 2]. Pick pivot = 5. Partition correctly: left part [3, 1, 2] labeled < pivot, right part [6, 8, 10] labeled > pivot. Include steps: START, base case length <= 1?, pick pivot, partition array, recursively sort left part, recursively sort right part, concatenate sorted-left + pivot + sorted-right, END. Modern vector style, white background, blue/orange accents, arrows, decision diamond, readable simple English labels. Avoid mathematical mistakes." \
  --image-model gpt-image-2-medium \
  --aspect-ratio landscape \
  -o generated/chatimg-gpt-image2-quicksort-flowchart.png \
  --timeout 300
```

## Python API

```python
from chatimg.image import create_generator

generator = create_generator("codex")
result = generator.generate("A cute cat astronaut")
```

## 配置

ChatImg 注册了 `chatenv.configs` entry point：

```toml
chatimg = "chatimg.config"
```

支持的主要环境变量：

- `OPENAI_API_BASE`, `OPENAI_API_KEY`, `OPENAI_IMAGE_MODEL`
- `CODEX_ACCESS_TOKEN`, `CODEX_REFRESH_TOKEN`, `CODEX_ACCESS_TOKEN_EXPIRES_AT`, `CODEX_OAUTH_BASE_URL`, `CODEX_API_BASE`, `CODEX_HOST_MODEL`, `CODEX_IMAGE_MODEL`
- `POLLINATIONS_API_KEY`, `POLLINATIONS_MODEL_ID`
- `SILICONFLOW_API_KEY`, `SILICONFLOW_MODEL_ID`
- `HUGGINGFACE_HUB_TOKEN`
- `LIBLIB_ACCESS_KEY`, `LIBLIB_SECRET_KEY`, `LIBLIB_MODEL_ID`
- `DASHSCOPE_API_KEY`

## 开发验证

```bash
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m chatimg.cli --help
PYTHONPATH=src python -m chatimg.cli codex list-models
python -m build
python -m twine check dist/*
```

## 发布状态

PyPI `ChatImg` 从 `0.1.x` 开始发布功能版本；`0.1.3` 是 Codex 配置 alias 修正 patch 版本。
