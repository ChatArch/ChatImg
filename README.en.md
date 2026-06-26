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

ChatImg is the ChatArch image-generation package. It carries the provider implementations previously exposed by the decoupled `chattool image` surface.

Supported providers:

- `codex` / `openai-codex`: ChatGPT/Codex OAuth image bridge with `gpt-image-2-*` presets.
- `pollinations`: Pollinations.ai image URL generation and model listing.
- `siliconflow`: SiliconFlow OpenAI-compatible image generation.
- `huggingface`: Hugging Face Inference image generation.
- `liblib`: LiblibAI signed API generation.
- `tongyi`: Tongyi Wanxiang / DashScope image generation.

## Install

Development install:

```bash
pip install -e ".[dev]"
```

Optional Tongyi/DashScope SDK extra:

```bash
pip install -e ".[images]"
```

## CLI

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
chatimg siliconflow generate "a cute dog" --size 1024x1024 -o dog.png
chatimg huggingface generate "A futuristic city at night" -o city.png
chatimg liblib generate "A cute dog" --model-id liblib-sdxl-model -o dog.png
chatimg tongyi generate "a cyberpunk cat" --size "1024*1024" -o cat.png
```

### Codex / GPT Image2 verified examples

The `codex` provider uses the ChatGPT/Codex OAuth-backed Responses API. The request payload uses the `image_generation` tool with model `gpt-image-2`. It is not the external Codex CLI.

Common configuration fields:

- `OPENAI_CODEX_ACCESS_TOKEN`: legacy Codex image access token variable; `OPENAI_ACCESS_TOKEN` is also supported.
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

ChatImg registers a `chatenv.configs` entry point:

```toml
chatimg = "chatimg.config"
```

Main supported environment variables:

- `OPENAI_ACCESS_TOKEN`, `OPENAI_CODEX_ACCESS_TOKEN`, `OPENAI_CODEX_AUTH_JSON`, `OPENAI_REFRESH_TOKEN`, `OPENAI_OAUTH_BASE_URL`, `OPENAI_ACCESS_TOKEN_EXPIRES_AT`, `OPENAI_IMAGE_MODEL`, `OPENAI_IMAGE_ASPECT_RATIO`, `OPENAI_CODEX_HOST_MODEL`, `OPENAI_CODEX_BASE_URL`, `OPENAI_CODEX_TIMEOUT`
- `POLLINATIONS_API_KEY`, `POLLINATIONS_MODEL_ID`
- `SILICONFLOW_API_KEY`, `SILICONFLOW_MODEL_ID`
- `HUGGINGFACE_HUB_TOKEN`
- `LIBLIB_ACCESS_KEY`, `LIBLIB_SECRET_KEY`, `LIBLIB_MODEL_ID`
- `DASHSCOPE_API_KEY`

## Development gates

```bash
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m chatimg.cli --help
PYTHONPATH=src python -m chatimg.cli codex list-models
python -m build
python -m twine check dist/*
```

## Release state

PyPI `chatimg==0.0.1` is a placeholder. Source version `0.1.0` is prepared as the first feature version, but tag / PyPI publishing requires separate approval.
