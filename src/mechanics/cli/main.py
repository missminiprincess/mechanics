"""Typer entrypoint for the mechanics package.

This module is introduced early in the refactor so the CLI surface can remain
stable while the implementation is moved into smaller modules.
"""

from __future__ import annotations

import typer

app = typer.Typer(
    add_completion=False,
    help="Run CR3BP simulations and generate report-ready visualizations.",
)


@app.command("info")
def info() -> None:
    """Print a short status line for the package bootstrap stage."""

    typer.echo("mechanics CLI is bootstrapped; simulation commands arrive in the next stage.")


def main() -> None:
    """Run the Typer application."""

    app()


if __name__ == "__main__":
    main()
