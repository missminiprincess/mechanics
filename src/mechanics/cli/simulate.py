"""CLI command for one simulation run."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from mechanics.core.models import SimulationConfig
from mechanics.core.simulate import run_simulation
from mechanics.core.systems import sun_earth_system
from mechanics.io.export import resolve_output_paths, save_json, save_lagrange_points
from mechanics.io.summary import simulation_summary
from mechanics.viz.interactive import save_dashboard
from mechanics.viz.static import plot_system_layout, plot_trajectory, plot_trajectory_3d


def simulate_command(
    point: str = typer.Option("L1", help="Selected point: L1, L2, L3, L4, or L5."),
    dx: float = typer.Option(1e-4, help="Initial x offset."),
    dy: float = typer.Option(0.0, help="Initial y offset."),
    dz: float = typer.Option(0.0, help="Initial z offset."),
    vx: float = typer.Option(0.0, help="Initial x velocity."),
    vy: float = typer.Option(0.0, help="Initial y velocity."),
    vz: float = typer.Option(0.0, help="Initial z velocity."),
    t_max: float = typer.Option(6.0, "--t-max", help="Final normalized time."),
    dt: float = typer.Option(0.002, help="Output time step."),
    sample_stride: int = typer.Option(
        6, "--sample-stride", help="Sampling stride for interactive outputs."
    ),
    output_stem: Optional[str] = typer.Option(None, "--output-stem", help="Base output name."),
) -> None:
    """Integrate one trajectory and save static outputs."""

    config = SimulationConfig(
        point_name=point,
        dx=dx,
        dy=dy,
        dz=dz,
        vx=vx,
        vy=vy,
        vz=vz,
        t_max=t_max,
        dt=dt,
        sample_stride=sample_stride,
    )
    result = run_simulation(sun_earth_system(), config)
    paths = resolve_output_paths()
    stem = output_stem or config.default_output_stem

    save_lagrange_points(result.points, paths.root / "sun_earth_lagrange_points_coordinates.json")
    save_json(simulation_summary(result), paths.runs_dir / f"{stem}.json")
    plot_system_layout(
        result.points, result.system, paths.figures_dir / "sun_earth_lagrange_points_map.png"
    )
    plot_trajectory(result, paths.figures_dir / f"{stem}_2d.png")
    plot_trajectory_3d(result, paths.figures_dir / f"{stem}_3d.png")
    save_dashboard(result, paths.html_dir / f"{stem}.html")

    typer.echo(f"Saved summary: {paths.runs_dir / f'{stem}.json'}")
    typer.echo(f"Saved 2D figure: {paths.figures_dir / f'{stem}_2d.png'}")
    typer.echo(f"Saved 3D figure: {paths.figures_dir / f'{stem}_3d.png'}")
    typer.echo(f"Saved interactive dashboard: {paths.html_dir / f'{stem}.html'}")


def run_single_case(stem: str, config: SimulationConfig, root: Optional[Path] = None) -> None:
    """Shared helper for showcase-style runs."""

    result = run_simulation(sun_earth_system(), config)
    paths = resolve_output_paths(root)
    save_json(simulation_summary(result), paths.runs_dir / f"{stem}.json")
    plot_trajectory(result, paths.figures_dir / f"{stem}_2d.png")
    plot_trajectory_3d(result, paths.figures_dir / f"{stem}_3d.png")
    save_dashboard(result, paths.html_dir / f"{stem}.html")
