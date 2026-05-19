"""Filesystem export helpers."""

import csv
import json
from pathlib import Path

from mechanics.core.analysis import distance_to_km, time_to_days
from mechanics.core.dynamics import jacobi_constant
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
        "t_days",
        "x",
        "y",
        "z",
        "x_km",
        "y_km",
        "z_km",
        "vx",
        "vy",
        "vz",
        "dx",
        "dy",
        "dz",
        "r_xy",
        "r_xy_km",
        "jacobi",
        "jacobi_delta",
    ]
    jacobi_values = jacobi_constant(result.states, result.system.mu)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        for time, state, rel, distance, jacobi in zip(
            result.times,
            result.states,
            result.rel_states,
            result.rel_distance_xy,
            jacobi_values,
            strict=True,
        ):
            writer.writerow(
                [
                    time,
                    time_to_days(result, float(time)),
                    state[0],
                    state[1],
                    state[2],
                    distance_to_km(result, float(state[0])),
                    distance_to_km(result, float(state[1])),
                    distance_to_km(result, float(state[2])),
                    state[3],
                    state[4],
                    state[5],
                    rel[0],
                    rel[1],
                    rel[2],
                    distance,
                    distance_to_km(result, float(distance)),
                    jacobi,
                    jacobi - jacobi_values[0],
                ]
            )
