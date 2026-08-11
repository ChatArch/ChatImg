from click.testing import CliRunner

from chatimg import __version__
from chatimg.cli import main


def test_version_option_reports_package_version():
    result = CliRunner().invoke(main, ["--version"])

    assert result.exit_code == 0
    assert f"chatimg, version {__version__}" in result.output


def test_help_exposes_tree_and_no_template_hello():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "--tree" in result.output
    assert "hello" not in result.output.lower()


def test_tree_option_renders_registered_image_provider_commands_and_no_template_hello():
    result = CliRunner().invoke(main, ["--tree"])

    assert result.exit_code == 0
    assert "chatimg # ChatImg image generation tools." in result.output
    assert "--tree # Print the registered command tree." in result.output
    for provider in (
        "codex",
        "huggingface",
        "liblib",
        "openai",
        "pollinations",
        "siliconflow",
        "tongyi",
    ):
        assert f"{provider} #" in result.output
    for leaf in (
        "codex generate",
        "codex auth-status",
        "openai generate",
        "pollinations list-models",
        "siliconflow generate",
        "huggingface generate",
        "liblib generate",
        "tongyi generate",
    ):
        assert leaf in result.output
    assert "hello" not in result.output.lower()
