"""Generate a clearer set of figures for the report and discussion."""

from __future__ import annotations

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


def run_case(stem: str, config: SimulationConfig) -> None:
    """Run one preconfigured demonstration case."""

    system = sun_earth_system()
    points = lagrange_points(system.mu)
    initial_state = initial_state_from_point(points[config.point_name], config)
    times, states = integrate_rk4(initial_state, system.mu, config.t_max, config.dt)

    root = Path(__file__).resolve().parents[2] / "results"
    figures_dir = root / "figures"
    animations_dir = root / "archive" / "html_animations"
    figures_dir.mkdir(parents=True, exist_ok=True)
    animations_dir.mkdir(parents=True, exist_ok=True)

    plot_trajectory(points, states, system, config, figures_dir / f"{stem}_2d.png")
    plot_trajectory_3d(points, states, system, config, figures_dir / f"{stem}_3d.png")
    save_animation_html(points, states, system, config, animations_dir / f"{stem}_animation.html")
    summary = simulation_summary(system, config, points, initial_state)
    summary["num_time_samples"] = len(times)
    save_summary(summary, root / f"{stem}_summary.json")


def main() -> None:
    """Generate all core explanatory visualizations."""

    system = sun_earth_system()
    points = lagrange_points(system.mu)
    root = Path(__file__).resolve().parents[2] / "results"
    figures_dir = root / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    save_lagrange_points(points, root / "sun_earth_lagrange_points_coordinates.json")
    plot_system_layout(points, system, figures_dir / "sun_earth_lagrange_points_map.png")

    # Unstable example near L1.
    run_case(
        "sun_earth_l1_unstable",
        SimulationConfig(point_name="L1", dx=1e-4, dy=0.0, vx=0.0, vy=0.0, t_max=20.0, dt=0.002, sample_stride=10),
    )

    # Stable example near L4.
    run_case(
        "sun_earth_l4_stable",
        SimulationConfig(point_name="L4", dx=1e-4, dy=0.0, vx=0.001, vy=0.001, t_max=12.0, dt=0.002, sample_stride=10),
    )

    print(f"Saved layout map: {figures_dir / 'sun_earth_lagrange_points_map.png'}")
    print(f"Saved unstable showcase: {figures_dir / 'sun_earth_l1_unstable_2d.png'}")
    print(f"Saved unstable 3D:       {figures_dir / 'sun_earth_l1_unstable_3d.png'}")
    print(f"Saved stable showcase:   {figures_dir / 'sun_earth_l4_stable_2d.png'}")
    print(f"Saved stable 3D:         {figures_dir / 'sun_earth_l4_stable_3d.png'}")


if __name__ == "__main__":
    main()
