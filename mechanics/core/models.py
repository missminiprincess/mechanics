"""Typed data models for the CR3BP simulation pipeline."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

LagrangePointMap = dict[str, np.ndarray]


@dataclass(frozen=True, slots=True)
class SystemParameters:
    """Normalized parameters of one CR3BP system."""

    name: str
    mu: float
    distance_m: float


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    """Configuration for one trajectory run near a Lagrange point."""

    point_name: str
    dx: float = 0.0
    dy: float = 0.0
    dz: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    t_max: float = 10.0
    dt: float = 0.002
    sample_stride: int = 4

    @property
    def mode_name(self) -> str:
        """Human-readable dynamical regime label for naming outputs."""

        return "unstable" if self.point_name in {"L1", "L2", "L3"} else "stable"

    @property
    def default_output_stem(self) -> str:
        """Default output name for one run."""

        return f"sun_earth_{self.point_name.lower()}_{self.mode_name}"


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """All computed state needed by visualization and export layers."""

    system: SystemParameters
    config: SimulationConfig
    points: LagrangePointMap
    point: np.ndarray
    initial_state: np.ndarray
    times: np.ndarray
    states: np.ndarray

    @property
    def point_name(self) -> str:
        """Selected Lagrange point name."""

        return self.config.point_name

    @property
    def rel_states(self) -> np.ndarray:
        """Trajectory in coordinates relative to the selected point."""

        return self.states[:, :3] - self.point

    @property
    def rel_distance_xy(self) -> np.ndarray:
        """Planar distance from the selected point."""

        rel = self.rel_states
        return np.hypot(rel[:, 0], rel[:, 1])


@dataclass(frozen=True, slots=True)
class OutputPaths:
    """Resolved filesystem targets for one simulation run."""

    root: Path
    runs_dir: Path
    figures_dir: Path
    html_dir: Path
