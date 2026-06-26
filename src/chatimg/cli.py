"""CLI entrypoint for chatimg."""

import click

from chatimg import __version__


@click.group()
@click.version_option(__version__, prog_name="chatimg")
def main() -> None:
    """chatimg command line interface."""
    # Add package-specific commands here. Prefer ChatStyle helpers for
    # interactive input when a command needs recoverable user input.


if __name__ == "__main__":
    main()
