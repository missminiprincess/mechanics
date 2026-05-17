"""Numerical integrators used in the project."""

from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp  # type: ignore[import-untyped]

from mechanics.core.dynamics import cr3bp_rhs


def integrate_trajectory(
    initial_state: np.ndarray,
    mu: float,
    t_max: float,
    dt: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Integrate the CR3BP equations on a fixed output grid."""

    num_steps = int(np.ceil(t_max / dt)) + 1
    times = np.linspace(0.0, dt * (num_steps - 1), num_steps)
    solution = solve_ivp(
        fun=lambda t, y: cr3bp_rhs(t, y, mu),
        t_span=(0.0, float(times[-1])),
        y0=initial_state,
        method="DOP853",
        t_eval=times,
        rtol=1e-10,
        atol=1e-12,
    )
    if not solution.success:
        raise RuntimeError(f"Integration failed: {solution.message}")
    return times, solution.y.T
