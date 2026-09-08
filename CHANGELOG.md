# Changelog

## 0.1.8 - 2026-09-08

### Added

- Add explicit `responses` mode to the reusable OpenAI/CRS API-key provider and CLI while retaining `images` as the compatible default.
- Add independent Responses carrier model selection via `host_model` / `--host-model`, defaulting to `gpt-5.5`, and isolated named ChatEnv OpenAI profile loading via `profile` / `--profile`.
- Add typed `CHATIMG_OPENAI_API_MODE` configuration (`images` by default).
- Require `chatenv>=0.2.10,<0.3.0` and load active OpenAI/ChatImg values through its public `EnvStore` paths.

### Verification

- Require a successful terminal Responses event plus a completed final image item; reject previews, failed/incomplete/truncated/malformed streams, and late errors without retrying.
- Decode complete SSE frames, including multiline `data:` fields, and reject unsupported Responses options before HTTP instead of silently dropping them.
- Cover API-key headers, payload model separation, profile precedence/isolation, response closing, Images compatibility, CLI signatures, docs, and version contracts.

## 0.1.7 - 2026-09-02

### Added

- Add the generated ChatImg logo asset to README and documentation surfaces.

### Verification

- Keep the logo as a local repository asset with no text, watermark, URL, or secret-like content.
- Re-run source tests, strict MkDocs, package build, Twine checks, and clean-install CLI readback.

## 0.1.6 - 2026-08-21

### Changed

- Migrate the top-level Click tree from ChatImg's local renderer to ChatStyle `add_tree_option()`, with `chatimg` fixed as the canonical public root.
- Keep parameter signatures in `chatimg --tree` and add `chatimg --tree-brief` for command-and-description-only output.
- Require `chatstyle>=0.2.0,<0.3.0` and `chatenv>=0.2.9,<0.3.0`.

### Verification

- Add regression coverage for the canonical root, default signatures, brief output, command nodes, and descriptions.
- Synchronize the bilingual README, documentation, and development guidance with the shared tree runtime.

## 0.1.5 - 2026-08-13

### Changed

- Move `chatimg codex` to the shared ChatEnv `OpenAI` profile lifecycle: runtime OAuth tokens are read from `tokens/OpenAI/<profile>.json`, and `envs/OpenAI/<profile>.env` is only the stable seed/fallback for OAuth/backend/model settings.
- Add `--profile` to `chatimg codex auth-status`, `auth-refresh`, `generate`, and `list-models`; token-store values take precedence over OpenAI env seed values.
- Remove the first-class `CodexConfig` ChatEnv namespace so users no longer maintain a separate `envs/Codex/.env` for ChatImg Codex image generation.
- Require `chatenv>=0.2.7` for token-store and token refresher compatibility.

### Verification

- Added regression tests for OpenAI profile token-store precedence, refresh persistence to `tokens/OpenAI/<profile>.json`, CLI `--profile`, and ignoring legacy `envs/Codex/.env`.
- Re-read the real `chatimg --tree` output and synchronized README/docs.

## 0.1.4 - 2026-07-31

### Added

- Add `chatimg --tree` output generated from the registered Click provider command surface.
- Add a first-class bilingual CLI tree documentation page and expose `--tree` in README/docs quick checks.
- Add `chatimg codex auth-status` and `chatimg codex auth-refresh` without exposing token values.
- Document the staged CRS API-key acceptance flow: regular Responses request first, then Images generation.

### Fixed

- Configure MkDocs Material emoji rendering and align package documentation URLs/Preview Docs links to the ChatArch public docs domain.
- Harden the PyPI publish workflow with tag/version/default-branch and duplicate-version guards.
- Allow Codex image generation from a refresh-only ChatEnv profile when no access token is present.
- Persist rotated access/refresh tokens back to the active Codex profile with mode `0600` while preserving host/image settings.
- Use the verified `gpt-5.5` Codex host model default.

### Verification

- CRS API key bound to a debug account passed `/responses` and generated a real `gpt-image-2` PNG through `chatimg openai generate`.
- Unit, syntax, CLI, and documentation gates cover the separate OAuth and API-key paths.

## 0.1.3 - 2026-07-07

### Fixed

- Remove `openai-codex` from `CodexConfig` ChatEnv aliases so `chatenv -t openai` resolves only to shared `OpenAIConfig` and does not become ambiguous with Codex.
- Keep `openai-codex` as a generator provider alias only; it is not a typed-env config alias.

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
