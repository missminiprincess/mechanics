"""High-level simulation pipeline."""

from __future__ import annotations

import numpy as np

from mechanics.core.integrators import integrate_trajectory
from mechanics.core.lagrange import lagrange_points
from mechanics.core.models import SimulationConfig, SimulationResult, SystemParameters


def initial_state_from_point(point: np.ndarray, config: SimulationConfig) -> np.ndarray:
    """Build the initial state from a Lagrange point plus user offsets."""

    return np.array(
        [
            point[0] + config.dx,
            point[1] + config.dy,
            point[2] + config.dz,
            config.vx,
            config.vy,
            config.vz,
        ],
        dtype=float,
    )


def run_simulation(system: SystemParameters, config: SimulationConfig) -> SimulationResult:
    """Run one simulation and return the full result object."""

    points = lagrange_points(system.mu)
    point = points[config.point_name]
    initial_state = initial_state_from_point(point, config)
    times, states = integrate_trajectory(initial_state, system.mu, config.t_max, config.dt)
    return SimulationResult(
        system=system,
        config=config,
        points=points,
        point=point,
        initial_state=initial_state,
        times=times,
        states=states,
    )
