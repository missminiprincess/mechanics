# ruff: noqa: E402,I001
"""Legacy compatibility module for the refactored package layout."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mechanics.core.dynamics import cr3bp_rhs, potential_derivatives
from mechanics.core.integrators import integrate_trajectory as integrate_rk4
from mechanics.core.lagrange import lagrange_points
from mechanics.core.models import SimulationConfig, SystemParameters
from mechanics.core.simulate import initial_state_from_point, run_simulation
from mechanics.core.systems import sun_earth_system
from mechanics.io.export import save_lagrange_points
from mechanics.io.summary import simulation_summary
from mechanics.viz.interactive import save_dashboard as save_animation_html
from mechanics.viz.static import plot_system_layout, plot_trajectory, plot_trajectory_3d


__all__ = [
    "SimulationConfig",
    "SystemParameters",
    "cr3bp_rhs",
    "initial_state_from_point",
    "integrate_rk4",
    "lagrange_points",
    "plot_system_layout",
    "plot_trajectory",
    "plot_trajectory_3d",
    "potential_derivatives",
    "run_simulation",
    "save_animation_html",
    "save_lagrange_points",
    "simulation_summary",
    "sun_earth_system",
]
