<div align="center">
    <img src="https://raw.githubusercontent.com/ChatArch/ChatImg/main/docs/assets/chatimg-logo.png" alt="ChatImg logo" width="120" />
</div>

<div align="center">
    <a href="https://pypi.python.org/pypi/ChatImg">
        <img src="https://img.shields.io/pypi/v/ChatImg.svg" alt="PyPI version" />
    </a>
    <a href="https://github.com/ChatArch/ChatImg/actions/workflows/ci.yml">
        <img src="https://github.com/ChatArch/ChatImg/actions/workflows/ci.yml/badge.svg" alt="Tests" />
    </a>
    <a href="https://arch.gh.wzhecnu.cn/ChatImg/">
        <img src="https://img.shields.io/badge/docs-mkdocs-blue.svg" alt="Documentation" />
    </a>
</div>

<div align="center">

[English](README.en.md) | [简体中文](README.md)
</div>

# ChatImg

ChatImg 是 ChatArch 的图片生成包，承接原 `chattool image` 中已经解耦的 provider 实现。

当前支持：

- `openai` / `crs`：OpenAI-compatible API-key 生图，兼容默认 Images，并支持显式 Responses 模式。
- `codex` / `openai-codex`：ChatGPT/Codex OAuth image bridge，复用 ChatEnv `OpenAI` profile + runtime token-store，支持 `gpt-image-2-*` preset。
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
chatimg --tree
chatimg --tree-brief
chatimg openai generate "a small red apple icon" -o apple.png
chatimg codex auth-status --profile work
chatimg codex auth-refresh --profile work
chatimg codex list-models
chatimg pollinations list-models
```

`chatimg --tree` 默认显示参数签名；`chatimg --tree-brief` 保留命令节点和描述，但省略参数签名。两种输出都由 ChatStyle 的共享 Click tree runtime 生成，并以公开 CLI 名 `chatimg` 作为根节点。

生成示例：

```bash
chatimg openai generate "a watercolor fox in the snow" --model gpt-image-2-medium --size 1024x1024 -o fox.png
chatimg codex generate "a watercolor fox in the snow" --profile work --aspect-ratio square -o fox-codex.png
chatimg pollinations generate "a cyberpunk cat" --model flux --width 512 --height 512 -o cat.png
chatimg siliconflow generate "a cute dog" --size 1024x1024 -o dog.png
chatimg huggingface generate "A futuristic city at night" -o city.png
chatimg liblib generate "A cute dog" --model-id liblib-sdxl-model -o dog.png
chatimg tongyi generate "一只赛博朋克猫" --size "1024*1024" -o cat.png
```

### OpenAI-compatible / CRS API-key 生图

`openai` provider 对齐 OpenAI 官方 Images API：`POST {OPENAI_API_BASE}/images/generations`。官方 base 是 `https://api.openai.com/v1`，因此完整官方接口是 `https://api.openai.com/v1/images/generations`。CRS 兼容服务可用自己的带 `/v1` base，例如 `https://crs.example/openai/v1`。

Images 保持兼容默认。若 CRS bridge 通过 `/responses` 返回最终图片，请显式使用 `--api-mode responses`。carrier `--host-model`（默认 `gpt-5.5`，也可来自 `OPENAI_API_MODEL`）与 image `--model` 独立。未指定 `--profile` 时，优先级为显式参数、进程环境、active ChatEnv profile、默认值；指定后只加载该 OpenAI profile，不激活，也不跨账号 fallback，显式参数仍优先。API mode 的顺序为显式参数、进程环境、active ChatImg profile、`images`。此 API-key 路径不读取 OAuth token 文件，也不会自动重试。Responses 会转发 `background`，未知 Python 扩展参数会在 HTTP 前被拒绝。

常用配置字段：

- `OPENAI_API_BASE`：OpenAI-compatible API base，必须包含 `/v1`。
- `OPENAI_API_KEY`：API key；不会 fallback 到 access token。
- `OPENAI_IMAGE_MODEL`：默认 image preset，例如 `gpt-image-2-medium`，会拆成 `model=gpt-image-2` 与 `quality=medium`。

```bash
chatenv use -t oai apple
chatimg openai generate "a small red apple icon" -o apple.png
```

CRS 验收建议分两步：先用同一个 API key 调普通 `/responses` 模型确认 key、账号绑定和模型路由，再调用 Images API。客户端始终只持有 `OPENAI_API_KEY`，不会读取或 fallback 到 OAuth access token。

```bash
chatimg openai generate \
  "A simple orange paper airplane over a pale blue grid, no text" \
  --api-mode responses \
  --profile work \
  --host-model gpt-5.5 \
  --model gpt-image-2-low \
  --quality low \
  --size 1024x1024 \
  -o generated/crs-api-key-image.png
```

### Codex / GPT Image2 实测示例

`codex` provider 走 ChatGPT/Codex OAuth-backed Responses API，请求里的 image tool model 是 `gpt-image-2`。它不是外部 Codex CLI。

`chatimg codex` 现在复用 ChatEnv 的 `OpenAI` profile 和 runtime token-store，不再需要维护单独的 Codex env 文件：

- runtime token-store：`~/.chatarch/tokens/OpenAI/<profile>.json`，包含 access/refresh token 等动态状态，并且优先级最高。
- stable seed：`~/.chatarch/envs/OpenAI/<profile>.env`（`default` profile 使用 active `OpenAI/.env`），只放 OAuth/backend/model seed 或 fallback。
- 常用 seed 字段：`OPENAI_OAUTH_BASE_URL`、`CHATGPT_BACKEND_BASE_URL`、`OPENAI_API_MODEL`、`OPENAI_IMAGE_MODEL`。
- 请求地址默认由 `CHATGPT_BACKEND_BASE_URL` 组合为 `${CHATGPT_BACKEND_BASE_URL}/codex/responses`。
- `openai`/`crs` API-key provider 仍只读取 `OPENAI_API_KEY`，不会 fallback 到 OAuth token。

可以显式指定 OpenAI profile：

```bash
chatimg codex auth-status --profile work
chatimg codex auth-refresh --profile work
chatimg codex generate "a small orange paper airplane" \
  --profile work \
  --host-model gpt-5.5 \
  --image-model gpt-image-2-low \
  -o generated/codex-image.png
```

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

generator = create_generator("codex", profile="work")
result = generator.generate("A cute cat astronaut")
```

## 配置

ChatImg 注册了 `chatenv.configs` entry point：

```toml
chatimg = "chatimg.config"
```

支持的主要环境变量：

- `OPENAI_API_BASE`, `OPENAI_API_KEY`, `OPENAI_IMAGE_MODEL`
- `OPENAI_OAUTH_BASE_URL`, `CHATGPT_BACKEND_BASE_URL`, `OPENAI_API_MODEL`, `OPENAI_IMAGE_MODEL` 作为 `OpenAI` profile seed；runtime OAuth tokens 由 `tokens/OpenAI/<profile>.json` 管理
- `POLLINATIONS_API_KEY`, `POLLINATIONS_MODEL_ID`
- `SILICONFLOW_API_KEY`, `SILICONFLOW_MODEL_ID`
- `HUGGINGFACE_HUB_TOKEN`
- `LIBLIB_ACCESS_KEY`, `LIBLIB_SECRET_KEY`, `LIBLIB_MODEL_ID`
- `DASHSCOPE_API_KEY`

## 开发验证

```bash
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m chatimg.image.cli --help
PYTHONPATH=src python -m chatimg.image.cli --tree
PYTHONPATH=src python -m chatimg.image.cli --tree-brief
PYTHONPATH=src python -m chatimg.image.cli codex list-models
python -m build
python -m twine check dist/*
```

## 发布状态

PyPI `ChatImg` 从 `0.1.x` 开始发布功能版本；`0.1.6` 将顶层 CLI tree 迁移到 ChatStyle 共享 runtime，默认树保留参数签名，并新增 `--tree-brief`。
