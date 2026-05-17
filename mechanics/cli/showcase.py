"""CLI command for a compact showcase run."""

import typer

from mechanics.cli.simulate import run_single_case
from mechanics.core.lagrange import lagrange_points
from mechanics.core.models import SimulationConfig
from mechanics.core.systems import sun_earth_system
from mechanics.io.export import resolve_output_paths, save_lagrange_points
from mechanics.viz.static import plot_system_layout


def showcase_command() -> None:
    """Generate the core report-ready static figures."""

    system = sun_earth_system()
    points = lagrange_points(system.mu)
    paths = resolve_output_paths()

    save_lagrange_points(points, paths.root / "sun_earth_lagrange_points_coordinates.json")
    plot_system_layout(points, system, paths.figures_dir / "sun_earth_lagrange_points_map.png")

    run_single_case(
        "sun_earth_l1_unstable",
        SimulationConfig(point_name="L1", dx=1e-4, t_max=20.0, dt=0.002, sample_stride=10),
    )
    run_single_case(
        "sun_earth_l4_stable",
        SimulationConfig(
            point_name="L4", dx=1e-4, vx=0.001, vy=0.001, t_max=12.0, dt=0.002, sample_stride=10
        ),
    )

    typer.echo(f"Saved layout map: {paths.figures_dir / 'sun_earth_lagrange_points_map.png'}")
    typer.echo(f"Saved showcase runs in: {paths.figures_dir}")
