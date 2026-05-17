"""Typer entrypoint for the mechanics package."""

import typer

from mechanics.cli.showcase import showcase_command
from mechanics.cli.simulate import simulate_command

app = typer.Typer(
    add_completion=False,
    help="Run CR3BP simulations and generate report-ready visualizations.",
)

app.command("simulate")(simulate_command)
app.command("showcase")(showcase_command)


def main() -> None:
    """Run the Typer application."""

    app()


if __name__ == "__main__":
    main()
