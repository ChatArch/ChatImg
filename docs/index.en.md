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
chatimg codex list-models
chatimg pollinations list-models
```

Generation examples:

```bash
chatimg codex generate "a watercolor fox in the snow" --aspect-ratio square -o fox.png
chatimg pollinations generate "a cyberpunk cat" --model flux --width 512 --height 512 -o cat.png
```

### Codex / GPT Image2 verified examples

The `codex` provider uses the ChatGPT/Codex OAuth-backed Responses API. The request payload uses the `image_generation` tool with model `gpt-image-2`. It is not the external Codex CLI.

Common configuration fields:

- `OPENAI_ACCESS_TOKEN`: OpenAI/ChatGPT OAuth access token for the Codex image path.
- `OPENAI_CODEX_AUTH_JSON`: Hermes auth.json path; defaults to `~/.hermes/auth.json` for reusing the local `openai-codex` login.
- `OPENAI_CODEX_HOST_MODEL`: host model that invokes the `image_generation` tool; defaults to `gpt-5.4`.
- `OPENAI_CODEX_BASE_URL`: Codex backend base URL; defaults to `https://chatgpt.com/backend-api/codex`.
- `OPENAI_CODEX_TIMEOUT`: request timeout in seconds; defaults to `300`.
- `OPENAI_IMAGE_MODEL`: default image preset; defaults to `gpt-image-2-medium`.
- `OPENAI_IMAGE_ASPECT_RATIO`: default aspect ratio; defaults to `square`.

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

Main fields: `OPENAI_*`, `OPENAI_CODEX_*`, `POLLINATIONS_*`, `SILICONFLOW_*`, `HUGGINGFACE_HUB_TOKEN`, `LIBLIB_*`, `DASHSCOPE_API_KEY`.

## Local preview

```bash
pip install -e ".[docs]"
mkdocs serve
```

Chinese version: [index.md](index.md).
