# ChatImg Documentation

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
chatimg openai generate "a small red apple icon" -o apple.png
chatimg codex list-models
chatimg pollinations list-models
```

Generation examples:

```bash
chatimg openai generate "a watercolor fox in the snow" --model gpt-image-2-medium --size 1024x1024 -o fox.png
chatimg codex generate "a watercolor fox in the snow" --aspect-ratio square -o fox-codex.png
chatimg pollinations generate "a cyberpunk cat" --model flux --width 512 --height 512 -o cat.png
```

### OpenAI-compatible / CRS Images API

The `openai` provider follows the OpenAI Images API shape: `POST {OPENAI_API_BASE}/images/generations`. The official base is `https://api.openai.com/v1`, so the full endpoint is `https://api.openai.com/v1/images/generations`.

```bash
chatenv use -t oai apple
chatimg openai generate "a small red apple icon" -o apple.png
```

### Codex / GPT Image2 verified examples

The `codex` provider uses the ChatGPT/Codex OAuth-backed Responses API. The request payload uses the `image_generation` tool with model `gpt-image-2`. It is not the external Codex CLI.

Common configuration fields:

- `CODEX_ACCESS_TOKEN`: Codex OAuth access token.
- `CODEX_REFRESH_TOKEN`: Codex OAuth refresh token used to refresh the access token.
- `CODEX_ACCESS_TOKEN_EXPIRES_AT`: UTC ISO timestamp for the access token expiry.
- `CODEX_OAUTH_BASE_URL`: Codex OAuth auth server base URL, defaulting to `https://auth.openai.com`.
- `CODEX_API_BASE`: Codex backend base URL, defaulting to `https://chatgpt.com/backend-api/codex`.
- `CODEX_HOST_MODEL`: host model that invokes the `image_generation` tool, defaulting to `gpt-5.4`.
- `CODEX_IMAGE_MODEL`: default image preset, defaulting to `gpt-image-2-medium`.

The `codex` provider no longer reads `~/.hermes/auth.json` and no longer maintains `OPENAI_CODEX_*` variables. `--timeout` and `--aspect-ratio` are command-level options, not long-lived env settings.

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

generator = create_generator("codex")
result = generator.generate("A cute cat astronaut")
```

## Configuration

ChatImg registers a ChatEnv `chatimg` config type. Run `chatenv test -t chatimg -I` for a side-effect-free schema check.

Main fields: `OPENAI_API_BASE` / `OPENAI_API_KEY` for the OpenAI-compatible Images API; `CODEX_*` for the Codex OAuth image bridge; other providers use `POLLINATIONS_*`, `SILICONFLOW_*`, `HUGGINGFACE_HUB_TOKEN`, `LIBLIB_*`, `DASHSCOPE_API_KEY`.

## Local preview

```bash
pip install -e ".[docs]"
mkdocs serve
```

Chinese version: [index.md](index.md).
