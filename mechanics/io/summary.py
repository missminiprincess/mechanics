"""Summary builders for simulation outputs."""

from mechanics.core.models import SimulationResult


def simulation_metrics(result: SimulationResult) -> dict[str, float | str | bool]:
    """Create derived metrics that make one run easier to interpret."""

    distances = result.rel_distance_xy
    initial_distance = float(distances[0])
    final_distance = float(distances[-1])
    max_index = int(distances.argmax())
    max_distance = float(distances[max_index])
    growth_ratio = max_distance / initial_distance if initial_distance > 0 else float("inf")
    stable_like = result.point_name in {"L4", "L5"} and max_distance < 0.05
    return {
        "regime_label": "неустойчивый" if result.point_name in {"L1", "L2", "L3"} else "устойчивый",
        "stable_like": stable_like,
        "initial_rel_distance_xy": initial_distance,
        "final_rel_distance_xy": final_distance,
        "max_rel_distance_xy": max_distance,
        "max_rel_distance_time": float(result.times[max_index]),
        "growth_ratio": growth_ratio,
    }


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
        **simulation_metrics(result),
    }
