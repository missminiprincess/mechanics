"""Command-line runner for the Sun-Earth Lagrange point project."""

from __future__ import annotations

import argparse
from pathlib import Path

from cr3bp import (
    SimulationConfig,
    initial_state_from_point,
    integrate_rk4,
    lagrange_points,
    plot_system_layout,
    plot_trajectory,
    plot_trajectory_3d,
    save_animation_html,
    save_lagrange_points,
    save_summary,
    simulation_summary,
    sun_earth_system,
)


def build_parser() -> argparse.ArgumentParser:
    """Create CLI arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Integrate a trajectory near any Sun-Earth Lagrange point and save "
            "static plots and archive the HTML animation separately."
        )
    )
    parser.add_argument("--point", default="L1", choices=["L1", "L2", "L3", "L4", "L5"])
    parser.add_argument("--dx", type=float, default=1e-4, help="Initial x offset from the selected point")
    parser.add_argument("--dy", type=float, default=0.0, help="Initial y offset from the selected point")
    parser.add_argument("--dz", type=float, default=0.0, help="Initial z offset from the selected point")
    parser.add_argument("--vx", type=float, default=0.0, help="Initial velocity along x")
    parser.add_argument("--vy", type=float, default=0.0, help="Initial velocity along y")
    parser.add_argument("--vz", type=float, default=0.0, help="Initial velocity along z")
    parser.add_argument("--t-max", type=float, default=6.0, help="Final normalized integration time")
    parser.add_argument("--dt", type=float, default=0.002, help="Time step for RK4")
    parser.add_argument("--sample-stride", type=int, default=6, help="Keep every N-th frame in the archived HTML animation")
    parser.add_argument(
        "--output-prefix",
        default=None,
        help="Base output name. Defaults to results named after the chosen point.",
    )
    return parser


def main() -> None:
    """Run one configured simulation."""

    parser = build_parser()
    args = parser.parse_args()

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

    system = sun_earth_system()
    points = lagrange_points(system.mu)
    initial_state = initial_state_from_point(points[config.point_name], config)
    times, states = integrate_rk4(initial_state, system.mu, config.t_max, config.dt)

    results_root = Path(__file__).resolve().parents[2] / "results"
    figures_dir = results_root / "figures"
    animations_dir = results_root / "archive" / "html_animations"
    figures_dir.mkdir(parents=True, exist_ok=True)
    animations_dir.mkdir(parents=True, exist_ok=True)

    default_mode = "unstable" if config.point_name in {"L1", "L2", "L3"} else "stable"
    prefix = args.output_prefix or f"sun_earth_{config.point_name.lower()}_{default_mode}"

    # Save shared data so the report can reference actual coordinates later.
    save_lagrange_points(points, results_root / "sun_earth_lagrange_points_coordinates.json")
    plot_system_layout(points, system, figures_dir / "sun_earth_lagrange_points_map.png")

    plot_trajectory(points, states, system, config, figures_dir / f"{prefix}.png")
    plot_trajectory_3d(points, states, system, config, figures_dir / f"{prefix}_3d.png")
    save_animation_html(points, states, system, config, animations_dir / f"{prefix}.html")

    summary = simulation_summary(system, config, points, initial_state)
    summary["num_time_samples"] = len(times)
    save_summary(summary, results_root / f"{prefix}_summary.json")

    print("Computed Sun-Earth Lagrange points:")
    for name, coords in points.items():
        print(f"  {name}: x={coords[0]: .12f}, y={coords[1]: .12f}, z={coords[2]: .12f}")
    print()
    print(f"Saved static plot:  {figures_dir / f'{prefix}.png'}")
    print(f"Saved 3D plot:      {figures_dir / f'{prefix}_3d.png'}")
    print(f"Archived animation: {animations_dir / f'{prefix}.html'}")
    print(f"Saved summary:      {results_root / f'{prefix}_summary.json'}")


if __name__ == "__main__":
    main()
