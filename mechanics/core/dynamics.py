"""Dynamics of the circular restricted three-body problem."""

import numpy as np


def potential_derivatives(state: np.ndarray, mu: float) -> np.ndarray:
    """Return spatial derivatives of the effective potential."""

    x, y, z = state[:3]
    x1 = -mu
    x2 = 1.0 - mu
    r1_sq = (x - x1) ** 2 + y**2 + z**2
    r2_sq = (x - x2) ** 2 + y**2 + z**2
    r1 = np.sqrt(r1_sq)
    r2 = np.sqrt(r2_sq)

    d_omega_dx = x - (1.0 - mu) * (x - x1) / r1**3 - mu * (x - x2) / r2**3
    d_omega_dy = y - (1.0 - mu) * y / r1**3 - mu * y / r2**3
    d_omega_dz = -(1.0 - mu) * z / r1**3 - mu * z / r2**3
    return np.array([d_omega_dx, d_omega_dy, d_omega_dz], dtype=float)


def effective_potential(state: np.ndarray, mu: float) -> float:
    """Return the CR3BP effective potential value."""

    x, y, z = state[:3]
    r1 = np.sqrt((x + mu) ** 2 + y**2 + z**2)
    r2 = np.sqrt((x - (1.0 - mu)) ** 2 + y**2 + z**2)
    return float(0.5 * (x**2 + y**2) + (1.0 - mu) / r1 + mu / r2)


def jacobi_constant(states: np.ndarray, mu: float) -> np.ndarray:
    """Return the Jacobi constant along one or more states."""

    values = np.atleast_2d(states)
    constants = []
    for state in values:
        speed_sq = float(np.dot(state[3:], state[3:]))
        constants.append(2.0 * effective_potential(state, mu) - speed_sq)
    return np.asarray(constants, dtype=float)


def cr3bp_rhs(_: float, state: np.ndarray, mu: float) -> np.ndarray:
    """Right-hand side of the first-order CR3BP system."""

    x_dot, y_dot, z_dot = state[3:]
    d_omega_dx, d_omega_dy, d_omega_dz = potential_derivatives(state, mu)
    return np.array(
        [
            x_dot,
            y_dot,
            z_dot,
            2.0 * y_dot + d_omega_dx,
            -2.0 * x_dot + d_omega_dy,
            d_omega_dz,
        ],
        dtype=float,
    )
