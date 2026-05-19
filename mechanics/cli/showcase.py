"""CLI command for a compact showcase run."""

import typer

from mechanics.cli.simulate import run_single_case
from mechanics.core.lagrange import lagrange_points
from mechanics.core.models import SimulationConfig
from mechanics.core.simulate import run_simulation
from mechanics.core.systems import available_system_names, get_system
from mechanics.io.export import resolve_output_paths, save_lagrange_points
from mechanics.viz.interactive import save_showcase_dashboard
from mechanics.viz.static import plot_system_layout


def showcase_command(
    system_name: str = typer.Option(
        "sun-earth",
        "--system",
        help=f"Physical system: {', '.join(available_system_names())}.",
    ),
) -> None:
    """Generate the core report-ready static figures."""

    try:
        system = get_system(system_name)
    except ValueError as exc:
        raise typer.BadParameter(str(exc), param_hint="--system") from exc

    points = lagrange_points(system.mu)
    paths = resolve_output_paths()
    slug = system.slug

    save_lagrange_points(points, paths.root / f"{slug}_lagrange_points_coordinates.json")
    plot_system_layout(points, system, paths.figures_dir / f"{slug}_lagrange_points_map.png")

    l1_result = run_single_case(
        f"{slug}_l1_unstable",
        SimulationConfig(point_name="L1", dx=1e-4, t_max=20.0, dt=0.002, sample_stride=10),
        system_name=system.name,
        save_html=False,
    )
    l4_result = run_single_case(
        f"{slug}_l4_stable",
        SimulationConfig(
            point_name="L4", dx=1e-4, vx=0.001, vy=0.001, t_max=12.0, dt=0.002, sample_stride=10
        ),
        system_name=system.name,
        save_html=False,
    )

    fair_results = [
        (
            "L1 dx=1e-4",
            run_simulation(
                system,
                SimulationConfig(point_name="L1", dx=1e-4, t_max=20.0, dt=0.002, sample_stride=10),
            ),
        ),
        (
            "L4 dx=1e-4",
            run_simulation(
                system,
                SimulationConfig(point_name="L4", dx=1e-4, t_max=20.0, dt=0.002, sample_stride=10),
            ),
        ),
    ]
    amplitude_results = [
        (
            f"{point} dx={dx:g}",
            run_simulation(
                system,
                SimulationConfig(point_name=point, dx=dx, t_max=12.0, dt=0.002, sample_stride=10),
            ),
        )
        for point in ("L1", "L4")
        for dx in (1e-5, 1e-4, 1e-3)
    ]
    dt_results = [
        (
            f"L1 dt={dt:g}",
            run_simulation(
                system,
                SimulationConfig(point_name="L1", dx=1e-4, t_max=12.0, dt=dt, sample_stride=10),
            ),
        )
        for dt in (0.004, 0.002, 0.001)
    ]
    save_showcase_dashboard(
        [l1_result, l4_result],
        paths.html_dir / f"{slug}_showcase.html",
        fair_results=fair_results,
        amplitude_results=amplitude_results,
        dt_results=dt_results,
    )

    typer.echo(f"Saved layout map: {paths.figures_dir / f'{slug}_lagrange_points_map.png'}")
    typer.echo(f"Saved showcase dashboard: {paths.html_dir / f'{slug}_showcase.html'}")
    typer.echo(f"Saved showcase runs in: {paths.figures_dir}")
