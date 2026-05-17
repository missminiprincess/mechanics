"""Summary builders for simulation outputs."""

from mechanics.core.models import SimulationResult


def simulation_summary(result: SimulationResult) -> dict[str, object]:
    """Create a compact metadata dictionary for one run."""

    return {
        "system": result.system.name,
        "mu": result.system.mu,
        "point_name": result.point_name,
        "point_coordinates": result.point.tolist(),
        "initial_state": result.initial_state.tolist(),
        "t_max": result.config.t_max,
        "dt": result.config.dt,
        "sample_stride": result.config.sample_stride,
        "num_time_samples": len(result.times),
        "max_rel_distance_xy": float(result.rel_distance_xy.max()),
    }
