"""Analysis helpers for interpreting CR3BP simulations."""

from collections.abc import Sequence

import numpy as np

from mechanics.core.dynamics import cr3bp_rhs
from mechanics.core.models import SimulationResult


def distance_to_km(result: SimulationResult, value: float) -> float:
    """Convert one normalized distance to kilometers."""

    return value * result.system.distance_m / 1000.0


def time_to_days(result: SimulationResult, value: float) -> float:
    """Convert one normalized CR3BP time value to days."""

    return value * result.system.time_unit_s / 86_400.0


def escape_time(result: SimulationResult, threshold: float | None = None) -> float | None:
    """Return the first normalized time at which the run crosses a distance threshold."""

    active_threshold = result.config.escape_threshold if threshold is None else threshold
    indices = np.flatnonzero(result.rel_distance_xy >= active_threshold)
    if len(indices) == 0:
        return None
    return float(result.times[int(indices[0])])


def linearized_eigenvalues(point_state: Sequence[float] | np.ndarray, mu: float) -> np.ndarray:
    """Return eigenvalues of the CR3BP first-order system near one state."""

    base = np.asarray(point_state, dtype=float)
    step = 1e-6
    jacobian = np.zeros((6, 6), dtype=float)
    for index in range(6):
        delta = np.zeros(6, dtype=float)
        delta[index] = step
        jacobian[:, index] = (
            cr3bp_rhs(0.0, base + delta, mu) - cr3bp_rhs(0.0, base - delta, mu)
        ) / (2.0 * step)
    return np.linalg.eigvals(jacobian)


def stability_label(eigenvalues: np.ndarray) -> str:
    """Return a compact stability label from linearized eigenvalues."""

    max_real = float(np.max(eigenvalues.real))
    return "линейно неустойчива" if max_real > 1e-6 else "линейно устойчива"
