# ruff: noqa: E402,I001
"""Legacy wrapper for one simulation run without a Typer dependency."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mechanics.core.models import SimulationConfig
from mechanics.core.simulate import run_simulation
from mechanics.core.systems import sun_earth_system
from mechanics.io.export import resolve_output_paths, save_json, save_lagrange_points
from mechanics.io.summary import simulation_summary
from mechanics.viz.interactive import save_dashboard
from mechanics.viz.static import plot_system_layout, plot_trajectory, plot_trajectory_3d


def build_parser() -> argparse.ArgumentParser:
    """Create CLI arguments for the compatibility entrypoint."""

    parser = argparse.ArgumentParser(description="Legacy wrapper for one mechanics simulation run.")
    parser.add_argument("--point", default="L1", choices=["L1", "L2", "L3", "L4", "L5"])
    parser.add_argument("--dx", type=float, default=1e-4)
    parser.add_argument("--dy", type=float, default=0.0)
    parser.add_argument("--dz", type=float, default=0.0)
    parser.add_argument("--vx", type=float, default=0.0)
    parser.add_argument("--vy", type=float, default=0.0)
    parser.add_argument("--vz", type=float, default=0.0)
    parser.add_argument("--t-max", type=float, default=6.0)
    parser.add_argument("--dt", type=float, default=0.002)
    parser.add_argument("--sample-stride", type=int, default=6)
    parser.add_argument("--output-stem", default=None)
    return parser


def main() -> None:
    """Run one simulation using the refactored package."""

    args = build_parser().parse_args()
    config = SimulationConfig(
        point_name=args.point,
        dx=args.dx,
        dy=args.dy,
        dz=args.dz,
        vx=args.vx,
        vy=args.vy,
        vz=args.vz,
        t_max=args.t_max,
        dt=args.dt,
        sample_stride=args.sample_stride,
    )
    result = run_simulation(sun_earth_system(), config)
    paths = resolve_output_paths()
    stem = args.output_stem or config.default_output_stem

    save_lagrange_points(result.points, paths.root / "sun_earth_lagrange_points_coordinates.json")
    save_json(simulation_summary(result), paths.runs_dir / f"{stem}.json")
    plot_system_layout(
        result.points,
        result.system,
        paths.figures_dir / "sun_earth_lagrange_points_map.png",
    )
    plot_trajectory(result, paths.figures_dir / f"{stem}_2d.png")
    plot_trajectory_3d(result, paths.figures_dir / f"{stem}_3d.png")
    save_dashboard(result, paths.html_dir / f"{stem}.html")

    print(f"Saved summary: {paths.runs_dir / f'{stem}.json'}")
    print(f"Saved 2D figure: {paths.figures_dir / f'{stem}_2d.png'}")
    print(f"Saved 3D figure: {paths.figures_dir / f'{stem}_3d.png'}")
    print(f"Saved interactive dashboard: {paths.html_dir / f'{stem}.html'}")


if __name__ == "__main__":
    main()
