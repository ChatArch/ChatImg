# Changelog

## 0.1.2 - 2026-07-07

### Changed

- Split Codex OAuth image configuration into a ChatImg-owned `CodexConfig` using `CODEX_*` fields instead of mixing Codex state into OpenAI-compatible `OPENAI_*` settings.
- Keep `OpenAIConfig` for the `openai` / `crs` Images API provider only; Codex provider now reads `CodexConfig`.
- Remove the `~/.hermes/auth.json` fallback and the `OPENAI_CODEX_AUTH_JSON` setting so ChatImg does not read Hermes credentials implicitly.
- Keep command-level details such as timeout and aspect ratio as CLI options or code defaults instead of long-lived environment variables.

### Verification

- Added tests that ensure `ChatImgConfig` has no OpenAI/Codex fields and that Codex does not read Hermes auth files.

## 0.1.1 - 2026-07-05

### Added

- Add `chatimg openai generate` and `openai` / `crs` providers for OpenAI-compatible Images API requests using `OPENAI_API_KEY`.
- Support active ChatEnv OpenAI profiles such as `chatenv use -t oai apple` for `OPENAI_API_BASE`, `OPENAI_API_KEY`, and `OPENAI_IMAGE_MODEL`.

### Changed

- Align the key-based image payload with the official `POST /v1/images/generations` shape.
- Require `chatenv>=0.2.2,<0.3.0`.
- Use only `OPENAI_ACCESS_TOKEN` for the Codex OAuth path; remove the confusing duplicate access-token setting.

### Verification

- Keep API key and access-token paths separate with no fallback between them.

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
- Codex image generation supports `OPENAI_ACCESS_TOKEN` and `~/.hermes/auth.json` fallback from the previous standalone Codex image workflow.

### Release notes

- PyPI `chatimg==0.0.1` remains the placeholder release.
- This `0.1.0` source state was tagged and published as the first feature release.
