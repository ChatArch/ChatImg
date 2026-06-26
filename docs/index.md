# ChatImg 文档

ChatImg 是 ChatArch 的图片生成包，承接原 `chattool image` 中已经解耦的 provider 实现。

## 支持的 provider

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
chatimg codex list-models
chatimg pollinations list-models
```

生成示例：

```bash
chatimg codex generate "a watercolor fox in the snow" --aspect-ratio square -o fox.png
chatimg pollinations generate "a cyberpunk cat" --model flux --width 512 --height 512 -o cat.png
```

### Codex / GPT Image2 实测示例

`codex` provider 走 ChatGPT/Codex OAuth-backed Responses API，请求里的 image tool model 是 `gpt-image-2`。它不是外部 Codex CLI。

常用配置字段：

- `OPENAI_CODEX_ACCESS_TOKEN`：历史 Codex image access token 变量；也兼容 `OPENAI_ACCESS_TOKEN`。
- `OPENAI_CODEX_AUTH_JSON`：Hermes auth.json 路径；默认 `~/.hermes/auth.json`，用于复用本机 `openai-codex` 登录态。
- `OPENAI_CODEX_HOST_MODEL`：承载 `image_generation` tool 的 host model，默认 `gpt-5.4`。
- `OPENAI_CODEX_BASE_URL`：Codex backend base URL，默认 `https://chatgpt.com/backend-api/codex`。
- `OPENAI_CODEX_TIMEOUT`：请求超时秒数，默认 `300`。
- `OPENAI_IMAGE_MODEL`：默认 image preset，默认 `gpt-image-2-medium`。
- `OPENAI_IMAGE_ASPECT_RATIO`：默认图片比例，默认 `square`。

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

ChatImg 通过 ChatEnv 注册 `chatimg` 配置类型。可用 `chatenv test -t chatimg -I` 做无网络 schema 检查。

主要字段：`OPENAI_*`、`OPENAI_CODEX_*`、`POLLINATIONS_*`、`SILICONFLOW_*`、`HUGGINGFACE_HUB_TOKEN`、`LIBLIB_*`、`DASHSCOPE_API_KEY`。

## 本地预览

```bash
pip install -e ".[docs]"
mkdocs serve
```

英文版见：[index.en.md](index.en.md)。
