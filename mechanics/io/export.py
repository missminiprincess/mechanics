"""Filesystem export helpers."""

import json
from pathlib import Path

from mechanics.core.models import LagrangePointMap, OutputPaths


def project_root() -> Path:
    """Return the repository root."""

    return Path(__file__).resolve().parents[2]


def resolve_output_paths(root: Path | None = None) -> OutputPaths:
    """Create and return output directories."""

    output_root = root or project_root() / "results"
    runs_dir = output_root / "runs"
    figures_dir = output_root / "figures"
    html_dir = output_root / "html"
    for path in (output_root, runs_dir, figures_dir, html_dir):
        path.mkdir(parents=True, exist_ok=True)
    return OutputPaths(
        root=output_root, runs_dir=runs_dir, figures_dir=figures_dir, html_dir=html_dir
    )


def save_json(payload: dict[str, object], path: Path) -> None:
    """Store one JSON payload."""

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def save_lagrange_points(points: LagrangePointMap, path: Path) -> None:
    """Store coordinates of the five Lagrange points."""

    payload = {name: coords.tolist() for name, coords in points.items()}
    save_json(payload, path)
