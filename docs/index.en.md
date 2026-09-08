# ChatImg Documentation

<p align="center">
  <img src="assets/chatimg-logo.png" alt="ChatImg logo" width="120" />
</p>

ChatImg is the ChatArch image-generation package. It carries the provider implementations previously exposed by the decoupled `chattool image` surface.

## Providers

- `codex` / `openai-codex`
- `pollinations`
- `siliconflow`
- `huggingface`
- `liblib`
- `tongyi`

## Common commands

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

`chatimg --tree` includes parameter signatures by default. `chatimg --tree-brief` keeps command nodes and descriptions while omitting signatures. Both views use the public CLI name `chatimg` as the root.

Generation examples:

```bash
chatimg openai generate "a watercolor fox in the snow" --model gpt-image-2-medium --size 1024x1024 -o fox.png
chatimg codex generate "a watercolor fox in the snow" --profile work --aspect-ratio square -o fox-codex.png
chatimg pollinations generate "a cyberpunk cat" --model flux --width 512 --height 512 -o cat.png
```

### OpenAI-compatible / CRS API-key images

The `openai` provider follows the OpenAI Images API shape: `POST {OPENAI_API_BASE}/images/generations`. The official base is `https://api.openai.com/v1`, so the full endpoint is `https://api.openai.com/v1/images/generations`.

Images remains the default. Use `--api-mode responses` for a CRS Responses bridge. Its carrier `--host-model` (default `gpt-5.5`, or `OPENAI_API_MODEL`) is independent of the image `--model`. Without `--profile`, precedence is explicit argument, process environment, active ChatEnv profile, then default. A named profile is isolated. API mode uses explicit argument, process environment, active ChatImg profile, then `images`. This path never reads OAuth token files or retries automatically; unsupported Responses options are rejected before HTTP.

```bash
chatenv use -t oai apple
chatimg openai generate "a small red apple icon" -o apple.png
```

For CRS API-key acceptance, first call a regular Responses model with the same key, then call the Images API. The `openai` provider only reads `OPENAI_API_KEY` and never falls back to an access token:

```bash
chatimg openai generate \
  --api-mode responses --profile work --host-model gpt-5.5 \
  "A simple orange paper airplane over a pale blue grid, no text" \
  --model gpt-image-2-low \
  --quality low \
  --size 1024x1024 \
  -o generated/crs-api-key-image.png
```

### Codex / GPT Image2 verified examples

The `codex` provider uses the ChatGPT/Codex OAuth-backed Responses API. The request payload uses the `image_generation` tool with model `gpt-image-2`. It is not the external Codex CLI.

`chatimg codex` now reuses ChatEnv's shared `OpenAI` profile and runtime token-store, so users no longer maintain a separate Codex env file:

- Runtime token-store: `~/.chatarch/tokens/OpenAI/<profile>.json`, containing dynamic access/refresh token state. These values have the highest priority.
- Stable seed: `~/.chatarch/envs/OpenAI/<profile>.env` (`default` uses active `OpenAI/.env`), used only for OAuth/backend/model seed or fallback values.
- Common seed fields: `OPENAI_OAUTH_BASE_URL`, `CHATGPT_BACKEND_BASE_URL`, `OPENAI_API_MODEL`, and `OPENAI_IMAGE_MODEL`.
- The request URL defaults to `${CHATGPT_BACKEND_BASE_URL}/codex/responses`.
- The `openai`/`crs` API-key provider still reads only `OPENAI_API_KEY` and never falls back to OAuth tokens.

Specify the OpenAI profile explicitly when needed:

```bash
chatimg codex auth-status --profile work
chatimg codex auth-refresh --profile work
chatimg codex generate "a small orange paper airplane" \
  --profile work \
  --host-model gpt-5.5 \
  --image-model gpt-image-2-low \
  -o generated/codex-image.png
```

Basic acceptance image:

```bash
chatimg codex generate \
  "A clean minimal ChatImg acceptance test illustration: a friendly robot holding a small picture frame, modern flat design, white background, no text" \
  --image-model gpt-image-2-low \
  --aspect-ratio square \
  -o generated/chatimg-gpt-image2-basic.png \
  --timeout 300
```

Quicksort flowchart:

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

## Configuration

ChatImg registers a ChatEnv `chatimg` config type. Run `chatenv test -t chatimg -I` for a side-effect-free schema check.

Main fields: `OPENAI_API_BASE` / `OPENAI_API_KEY` for the OpenAI-compatible Images API; `OPENAI_OAUTH_BASE_URL` / `CHATGPT_BACKEND_BASE_URL` / `OPENAI_API_MODEL` / `OPENAI_IMAGE_MODEL` for the OpenAI profile seed; runtime OAuth tokens live in `tokens/OpenAI/<profile>.json`; other providers use `POLLINATIONS_*`, `SILICONFLOW_*`, `HUGGINGFACE_HUB_TOKEN`, `LIBLIB_*`, `DASHSCOPE_API_KEY`.

## Local preview

```bash
pip install -e ".[docs]"
mkdocs serve
```

CLI tree: [CLI Tree](cli-tree.md).
