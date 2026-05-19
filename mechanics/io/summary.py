"""Summary builders for simulation outputs."""

from mechanics.core.analysis import (
    distance_to_km,
    escape_time,
    linearized_eigenvalues,
    stability_label,
    time_to_days,
)
from mechanics.core.dynamics import jacobi_constant
from mechanics.core.models import SimulationResult


def simulation_metrics(result: SimulationResult) -> dict[str, float | str | bool | None]:
    """Create derived metrics that make one run easier to interpret."""

    distances = result.rel_distance_xy
    initial_distance = float(distances[0])
    final_distance = float(distances[-1])
    max_index = int(distances.argmax())
    max_distance = float(distances[max_index])
    growth_ratio = max_distance / initial_distance if initial_distance > 0 else float("inf")
    stable_like = result.point_name in {"L4", "L5"} and max_distance < 0.05
    escape_at = escape_time(result)
    jacobi_values = jacobi_constant(result.states, result.system.mu)
    jacobi_delta = jacobi_values - jacobi_values[0]
    eigenvalues = linearized_eigenvalues(
        [result.point[0], result.point[1], result.point[2], 0.0, 0.0, 0.0],
        result.system.mu,
    )
    max_real_eigenvalue = float(max(eigenvalues.real))
    return {
        "regime_label": "неустойчивый" if result.point_name in {"L1", "L2", "L3"} else "устойчивый",
        "stable_like": stable_like,
        "initial_rel_distance_xy": initial_distance,
        "initial_rel_distance_km": distance_to_km(result, initial_distance),
        "final_rel_distance_xy": final_distance,
        "final_rel_distance_km": distance_to_km(result, final_distance),
        "max_rel_distance_xy": max_distance,
        "max_rel_distance_km": distance_to_km(result, max_distance),
        "max_rel_distance_time": float(result.times[max_index]),
        "max_rel_distance_time_days": time_to_days(result, float(result.times[max_index])),
        "growth_ratio": growth_ratio,
        "escape_threshold": result.config.escape_threshold,
        "escape_threshold_km": distance_to_km(result, result.config.escape_threshold),
        "escape_time": escape_at,
        "escape_time_days": None if escape_at is None else time_to_days(result, escape_at),
        "jacobi_initial": float(jacobi_values[0]),
        "jacobi_delta_max_abs": float(abs(jacobi_delta).max()),
        "linear_max_real_eigenvalue": max_real_eigenvalue,
        "linear_stability": stability_label(eigenvalues),
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
        "distance_unit_km": result.system.distance_m / 1000.0,
        "time_unit_days": result.system.time_unit_s / 86_400.0,
        "num_time_samples": len(result.times),
        **simulation_metrics(result),
    }
