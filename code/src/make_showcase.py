# ruff: noqa: E402,I001
"""Legacy wrapper for the showcase run without a Typer dependency."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mechanics.core.lagrange import lagrange_points
from mechanics.core.models import SimulationConfig
from mechanics.core.simulate import run_simulation
from mechanics.core.systems import sun_earth_system
from mechanics.io.export import resolve_output_paths, save_json, save_lagrange_points
from mechanics.io.summary import simulation_summary
from mechanics.viz.interactive import save_dashboard
from mechanics.viz.static import plot_system_layout, plot_trajectory, plot_trajectory_3d


def run_case(stem: str, config: SimulationConfig) -> None:
    """Run one fixed showcase case."""

    result = run_simulation(sun_earth_system(), config)
    paths = resolve_output_paths()
    save_json(simulation_summary(result), paths.runs_dir / f"{stem}.json")
    plot_trajectory(result, paths.figures_dir / f"{stem}_2d.png")
    plot_trajectory_3d(result, paths.figures_dir / f"{stem}_3d.png")
    save_dashboard(result, paths.html_dir / f"{stem}.html")


def main() -> None:
    """Generate the static and interactive showcase outputs."""

    system = sun_earth_system()
    points = lagrange_points(system.mu)
    paths = resolve_output_paths()

    save_lagrange_points(points, paths.root / "sun_earth_lagrange_points_coordinates.json")
    plot_system_layout(points, system, paths.figures_dir / "sun_earth_lagrange_points_map.png")
    run_case(
        "sun_earth_l1_unstable",
        SimulationConfig(point_name="L1", dx=1e-4, t_max=20.0, dt=0.002, sample_stride=10),
    )
    run_case(
        "sun_earth_l4_stable",
        SimulationConfig(
            point_name="L4",
            dx=1e-4,
            vx=0.001,
            vy=0.001,
            t_max=12.0,
            dt=0.002,
            sample_stride=10,
        ),
    )
    print(f"Saved layout map: {paths.figures_dir / 'sun_earth_lagrange_points_map.png'}")
    print(f"Saved showcase runs in: {paths.figures_dir}")


if __name__ == "__main__":
    main()
