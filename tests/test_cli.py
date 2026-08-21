from click.testing import CliRunner

from chatimg import __version__
from chatimg.cli import main


def test_version_option_reports_package_version():
    result = CliRunner().invoke(main, ["--version"])

    assert result.exit_code == 0
    assert f"chatimg, version {__version__}" in result.output


def test_help_exposes_tree_modes_and_no_template_hello():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "--tree" in result.output
    assert "--tree-brief" in result.output
    assert "hello" not in result.output.lower()


def test_tree_option_renders_signatures_registered_commands_and_canonical_root():
    result = CliRunner().invoke(main, ["--tree"])

    assert result.exit_code == 0
    assert result.output.splitlines()[0] == "chatimg"
    assert "--tree  # Print the registered CLI tree and exit." in result.output
    assert (
        "--tree-brief  # Print the registered CLI tree without parameter signatures and exit."
        in result.output
    )
    for provider in (
        "codex",
        "huggingface",
        "liblib",
        "openai",
        "pollinations",
        "siliconflow",
        "tongyi",
    ):
        assert f"{provider}  #" in result.output
    for signature in (
        "auth-status [--profile PROFILE]",
        "generate [PROMPT] [--aspect-ratio ASPECT-RATIO]",
        "generate [PROMPT] [--model IMAGE-MODEL]",
        "generate [PROMPT] [--model MODEL]",
        "generate [PROMPT] [--output OUTPUT]",
        "generate [PROMPT] [--model-id MODEL-ID]",
        "generate [PROMPT] [--style STYLE]",
    ):
        assert signature in result.output
    assert "hello" not in result.output.lower()


def test_tree_brief_omits_signatures_but_keeps_commands_and_descriptions():
    result = CliRunner().invoke(main, ["--tree-brief"])

    assert result.exit_code == 0
    assert result.output.splitlines()[0] == "chatimg"
    assert "[" not in result.output
    assert "codex  # ChatGPT/Codex OAuth image tools." in result.output
    assert (
        "auth-status  # Show safe OpenAI OAuth profile status without token values."
        in result.output
    )
    assert (
        "generate  # Generate an image using the ChatGPT/Codex OAuth image bridge."
        in result.output
    )
    assert "list-models  # List available image models for Pollinations.ai." in result.output
