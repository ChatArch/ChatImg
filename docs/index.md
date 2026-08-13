# ChatImg 文档

ChatImg 是 ChatArch 的图片生成包，承接原 `chattool image` 中已经解耦的 provider 实现。

## 支持的 provider

- `openai` / `crs`
- `codex` / `openai-codex`
- `pollinations`
- `siliconflow`
- `huggingface`
- `liblib`
- `tongyi`

## 常用命令

```bash
chatimg --help
chatimg --version
chatimg --tree
chatimg openai generate "a small red apple icon" -o apple.png
chatimg codex auth-status --profile work
chatimg codex auth-refresh --profile work
chatimg codex list-models
chatimg pollinations list-models
```

生成示例：

```bash
chatimg openai generate "a watercolor fox in the snow" --model gpt-image-2-medium --size 1024x1024 -o fox.png
chatimg codex generate "a watercolor fox in the snow" --profile work --aspect-ratio square -o fox-codex.png
chatimg pollinations generate "a cyberpunk cat" --model flux --width 512 --height 512 -o cat.png
```

### OpenAI-compatible / CRS Images API

`openai` provider 对齐 OpenAI 官方 Images API：`POST {OPENAI_API_BASE}/images/generations`。官方 base 是 `https://api.openai.com/v1`，完整接口是 `https://api.openai.com/v1/images/generations`。

```bash
chatenv use -t oai apple
chatimg openai generate "a small red apple icon" -o apple.png
```

CRS API-key 验收应先用同一个 key 调普通 Responses 模型，再调 Images API。`openai` provider 只读取 `OPENAI_API_KEY`，不会 fallback 到 access token：

```bash
chatimg openai generate \
  "A simple orange paper airplane over a pale blue grid, no text" \
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

ChatImg 通过 ChatEnv 注册 `chatimg` 配置类型。可用 `chatenv test -t chatimg -I` 做无网络 schema 检查。

主要字段：`OPENAI_API_BASE` / `OPENAI_API_KEY` 用于 OpenAI-compatible Images API；`OPENAI_OAUTH_BASE_URL` / `CHATGPT_BACKEND_BASE_URL` / `OPENAI_API_MODEL` / `OPENAI_IMAGE_MODEL` 用于 OpenAI profile seed；runtime OAuth tokens 写入 `tokens/OpenAI/<profile>.json`；其他 provider 使用 `POLLINATIONS_*`、`SILICONFLOW_*`、`HUGGINGFACE_HUB_TOKEN`、`LIBLIB_*`、`DASHSCOPE_API_KEY`。

## 本地预览

```bash
pip install -e ".[docs]"
mkdocs serve
```

CLI 树见：[CLI 树](cli-tree.md)。
