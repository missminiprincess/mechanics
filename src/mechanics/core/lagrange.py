"""Lagrange point computation."""

from __future__ import annotations

import numpy as np
from scipy.optimize import root_scalar  # type: ignore[import-untyped]

from mechanics.core.models import LagrangePointMap


def _collinear_equation(x: float, mu: float) -> float:
    """Equation whose roots define the collinear points L1, L2, L3."""

    r1 = abs(x + mu)
    r2 = abs(x - (1.0 - mu))
    return x - (1.0 - mu) * (x + mu) / r1**3 - mu * (x - (1.0 - mu)) / r2**3


def _solve_collinear(mu: float, left: float, right: float) -> float:
    """Solve one bracketing root problem robustly."""

    solution = root_scalar(
        lambda x: _collinear_equation(x, mu),
        bracket=(left, right),
        method="bisect",
        xtol=1e-13,
        maxiter=200,
    )
    if not solution.converged:
        raise RuntimeError(f"Failed to converge for bracket [{left}, {right}]")
    return float(solution.root)


def lagrange_points(mu: float) -> LagrangePointMap:
    """Compute coordinates of the five Lagrange points."""

    x1 = -mu
    x2 = 1.0 - mu
    eps = 1e-6

    l1_x = _solve_collinear(mu, x1 + eps, x2 - eps)
    l2_x = _solve_collinear(mu, x2 + eps, 2.0)
    l3_x = _solve_collinear(mu, -2.0, x1 - eps)

    return {
        "L1": np.array([l1_x, 0.0, 0.0], dtype=float),
        "L2": np.array([l2_x, 0.0, 0.0], dtype=float),
        "L3": np.array([l3_x, 0.0, 0.0], dtype=float),
        "L4": np.array([0.5 - mu, np.sqrt(3.0) / 2.0, 0.0], dtype=float),
        "L5": np.array([0.5 - mu, -np.sqrt(3.0) / 2.0, 0.0], dtype=float),
    }
