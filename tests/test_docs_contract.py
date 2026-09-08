from pathlib import Path


def test_mkdocs_uses_chatarch_public_domain_i18n_and_material_icon_renderer():
    config = Path("mkdocs.yml").read_text(encoding="utf-8")

    assert "site_url: https://arch.gh.wzhecnu.cn/ChatImg/" in config
    assert "name: material" in config
    assert "mkdocs-static-i18n" in Path("pyproject.toml").read_text(encoding="utf-8")
    assert "pymdownx.emoji" in config
    assert "material.extensions.emoji.twemoji" in config
    assert "material.extensions.emoji.to_svg" in config
    assert "cli-tree.md" in config
    assert "ChatImg/en/" in config


def test_public_docs_use_portable_openai_profile_examples():
    public_docs = [
        Path("README.md"),
        Path("README.en.md"),
        Path("docs/index.md"),
        Path("docs/index.en.md"),
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in public_docs)

    assert "--profile work" in text
    assert "73-wzh" not in text
    assert "/Users/rexwzh" not in text
    assert "/home/zhihong" not in text
    assert "chatenv use -t codex" not in text
    assert "envs/Codex/.env" not in text
    assert "CODEX_ACCESS_TOKEN" not in text
    assert "CODEX_REFRESH_TOKEN" not in text
    assert "CODEX_API_BASE" not in text
    assert "CODEX_OAUTH_BASE_URL" not in text


def test_logo_asset_is_documented_and_local():
    logo = Path("docs/assets/chatimg-logo.png")
    assert logo.exists()
    assert logo.stat().st_size > 1000

    for path in [Path("README.md"), Path("README.en.md"), Path("docs/index.md"), Path("docs/index.en.md")]:
        text = path.read_text(encoding="utf-8")
        assert "chatimg-logo.png" in text


def test_responses_cli_contract_is_in_bilingual_docs():
    paths = [Path("README.md"), Path("README.en.md"), Path("docs/index.md"), Path("docs/index.en.md")]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "--api-mode responses" in text
        assert "--host-model gpt-5.5" in text
        assert "--profile work" in text
    for path in [Path("docs/cli-tree.md"), Path("docs/cli-tree.en.md")]:
        text = path.read_text(encoding="utf-8")
        assert "[--api-mode API-MODE] [--profile PROFILE] [--host-model HOST-MODEL]" in text
