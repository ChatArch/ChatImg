from click.testing import CliRunner

from chatimg import __version__
from chatimg.cli import main


def test_version_option_reports_package_version():
    result = CliRunner().invoke(main, ["--version"])

    assert result.exit_code == 0
    assert f"chatimg, version {__version__}" in result.output
