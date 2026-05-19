"""CLI command for one simulation run."""

from pathlib import Path

import typer

from mechanics.core.models import SimulationConfig, SimulationResult
from mechanics.core.simulate import run_simulation
from mechanics.core.systems import available_system_names, get_system
from mechanics.io.export import (
    resolve_output_paths,
    save_json,
    save_lagrange_points,
    save_trajectory_csv,
)
from mechanics.io.summary import simulation_summary
from mechanics.viz.interactive import save_dashboard
from mechanics.viz.static import plot_system_layout, plot_trajectory, plot_trajectory_3d


def simulate_command(
    system_name: str = typer.Option(
        "sun-earth",
        "--system",
        help=f"Physical system: {', '.join(available_system_names())}.",
    ),
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
    output_stem: str | None = typer.Option(None, "--output-stem", help="Base output name."),
) -> None:
    """Integrate one trajectory and save static outputs."""

    try:
        system = get_system(system_name)
    except ValueError as exc:
        raise typer.BadParameter(str(exc), param_hint="--system") from exc

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
    result = run_simulation(system, config)
    paths = resolve_output_paths()
    stem = output_stem or f"{system.slug}_{config.point_name.lower()}_{config.mode_name}"

    save_lagrange_points(
        result.points, paths.root / f"{system.slug}_lagrange_points_coordinates.json"
    )
    save_json(simulation_summary(result), paths.runs_dir / f"{stem}.json")
    save_trajectory_csv(result, paths.runs_dir / f"{stem}_trajectory.csv")
    plot_system_layout(
        result.points, result.system, paths.figures_dir / f"{system.slug}_lagrange_points_map.png"
    )
    plot_trajectory(result, paths.figures_dir / f"{stem}_2d.png")
    plot_trajectory_3d(result, paths.figures_dir / f"{stem}_3d.png")
    save_dashboard(result, paths.html_dir / f"{stem}.html")

    typer.echo(f"Saved summary: {paths.runs_dir / f'{stem}.json'}")
    typer.echo(f"Saved trajectory CSV: {paths.runs_dir / f'{stem}_trajectory.csv'}")
    typer.echo(f"Saved 2D figure: {paths.figures_dir / f'{stem}_2d.png'}")
    typer.echo(f"Saved 3D figure: {paths.figures_dir / f'{stem}_3d.png'}")
    typer.echo(f"Saved interactive dashboard: {paths.html_dir / f'{stem}.html'}")


def run_single_case(
    stem: str,
    config: SimulationConfig,
    system_name: str = "sun-earth",
    root: Path | None = None,
    save_html: bool = True,
) -> SimulationResult:
    """Shared helper for showcase-style runs."""

    system = get_system(system_name)
    result = run_simulation(system, config)
    paths = resolve_output_paths(root)
    save_json(simulation_summary(result), paths.runs_dir / f"{stem}.json")
    save_trajectory_csv(result, paths.runs_dir / f"{stem}_trajectory.csv")
    plot_trajectory(result, paths.figures_dir / f"{stem}_2d.png")
    plot_trajectory_3d(result, paths.figures_dir / f"{stem}_3d.png")
    if save_html:
        save_dashboard(result, paths.html_dir / f"{stem}.html")
    return result
