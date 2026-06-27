# Changelog

## 0.1.0 - 2026-06-27

### Added

- Bootstrap ChatImg as a ChatArch Python package with `chatimg` CLI, ChatEnv config registration, CI/docs/publish workflows, and Trusted Publisher-ready metadata.
- Migrate the decoupled ChatTool image provider surface into `chatimg.image`:
  - Codex / OpenAI OAuth image bridge
  - Pollinations
  - SiliconFlow
  - Hugging Face
  - LiblibAI
  - Tongyi / DashScope
- Add reusable Python API via `chatimg.image.create_generator()` and provider classes.
- Add `chatimg codex|pollinations|siliconflow|huggingface|liblib|tongyi` CLI groups.
- Document verified GPT Image2 Codex examples, including a basic acceptance image and quicksort flowchart command.

### Changed

- ChatImg owns image provider configuration through `ChatImgConfig` and the `chatenv.configs` entry point.
- Codex image generation now supports legacy `OPENAI_CODEX_*` variables and `~/.hermes/auth.json` fallback from the previous standalone Codex image workflow.

### Release notes

- PyPI `chatimg==0.0.1` remains the placeholder release.
- This `0.1.0` source state has not been tagged or published yet.
