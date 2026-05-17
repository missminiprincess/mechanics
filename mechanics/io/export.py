"""Filesystem export helpers."""

import csv
import json
from pathlib import Path

from mechanics.core.models import LagrangePointMap, OutputPaths, SimulationResult


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


def save_trajectory_csv(result: SimulationResult, path: Path) -> None:
    """Store the full simulated trajectory as analysis-ready CSV."""

    header = [
        "t",
        "x",
        "y",
        "z",
        "vx",
        "vy",
        "vz",
        "dx",
        "dy",
        "dz",
        "r_xy",
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        for time, state, rel, distance in zip(
            result.times, result.states, result.rel_states, result.rel_distance_xy, strict=True
        ):
            writer.writerow(
                [
                    time,
                    state[0],
                    state[1],
                    state[2],
                    state[3],
                    state[4],
                    state[5],
                    rel[0],
                    rel[1],
                    rel[2],
                    distance,
                ]
            )
