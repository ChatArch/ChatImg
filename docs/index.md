# ChatImg 文档

<p align="center">
  <img src="assets/chatimg-logo.png" alt="ChatImg logo" width="120" />
</p>

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
chatimg --tree-brief
chatimg openai generate "a small red apple icon" -o apple.png
chatimg codex auth-status --profile work
chatimg codex auth-refresh --profile work
chatimg codex list-models
chatimg pollinations list-models
```

`chatimg --tree` 默认显示参数签名；`chatimg --tree-brief` 保留命令节点和描述，但省略参数签名。两种输出都以公开 CLI 名 `chatimg` 作为根节点。

生成示例：

```bash
chatimg openai generate "a watercolor fox in the snow" --model gpt-image-2-medium --size 1024x1024 -o fox.png
chatimg codex generate "a watercolor fox in the snow" --profile work --aspect-ratio square -o fox-codex.png
chatimg pollinations generate "a cyberpunk cat" --model flux --width 512 --height 512 -o cat.png
```

### OpenAI-compatible / CRS API-key 生图

`openai` provider 对齐 OpenAI 官方 Images API：`POST {OPENAI_API_BASE}/images/generations`。官方 base 是 `https://api.openai.com/v1`，完整接口是 `https://api.openai.com/v1/images/generations`。

Images 保持默认。CRS Responses bridge 使用 `--api-mode responses`；carrier `--host-model`（默认 `gpt-5.5`，或读取 `OPENAI_API_MODEL`）与 image `--model` 独立。未指定 `--profile` 时按显式参数、进程环境、active ChatEnv profile、默认值取值；命名 profile 相互隔离。API mode 按显式参数、进程环境、active ChatImg profile、`images` 取值。该路径不读取 OAuth token 文件，也不自动重试；不支持的 Responses 参数会在 HTTP 前报错。

```bash
chatenv use -t oai apple
chatimg openai generate "a small red apple icon" -o apple.png
```

CRS API-key 验收应先用同一个 key 调普通 Responses 模型，再调 Images API。`openai` provider 只读取 `OPENAI_API_KEY`，不会 fallback 到 access token：

```bash
chatimg openai generate \
  --api-mode responses --profile work --host-model gpt-5.5 \
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

## 本地四图菱形拼接

```bash
chatimg collage diamond 1.png 2.png 3.png 4.png -o collage.png
chatimg collage diamond 1.png 2.png 3.png 4.png --tile-height 600 -o large.png
```

四张输入必须是至少 2×2 像素的方图，按参数顺序对应图 1～4；尺寸可不同，不会自动裁成方图。每图按左上、右上、右下、左下切块，分别旋转 -45°、45°、135°、225°并拉伸为菱形。图 1/2 铺第一层，图 3/4 横纵错开半块填入空隙；每行重复首块，并保留边界裁剪。这不是普通四宫格。

默认块高 300、块宽 `int(300 * 1.426)`，输出 **1921×750**；`--tile-height` 支持 2～2000。奇数边长不丢末行/末列，半块偏移保留亚像素精度，避免黑缝。输入透明度只合成一次，最终铺在黑底上，输出 RGB 图片。

纯本地 Pillow 处理，不调用生图 API、不需要 Key/profile，也不写中间图片。`-o` 为必填，支持 PNG/JPEG/WebP；已有输出（包括输入原图）不会被覆盖，请另选文件名。

```python
from chatimg.collage import save_diamond_collage

output = save_diamond_collage(
    ["1.png", "2.png", "3.png", "4.png"], "collage.png", tile_height=300
)
```

`create_diamond_collage(images, tile_height=300)` 接受路径或 Pillow 图片，返回新的 Pillow RGB 图片，不修改输入；`save_diamond_collage` 负责创建输出父目录、保存和返回路径。

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
