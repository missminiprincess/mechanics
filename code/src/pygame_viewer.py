"""Deprecated pygame entrypoint kept only to point at the new workflow."""

from __future__ import annotations


def main() -> None:
    """Explain how to use the new interactive workflow."""

    raise SystemExit(
        "pygame viewer retired. Use `python -m mechanics.cli.main simulate ...` "
        "and open the generated file in `results/html/*.html`."
    )


if __name__ == "__main__":
    main()
