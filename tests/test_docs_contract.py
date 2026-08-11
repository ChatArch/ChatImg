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
