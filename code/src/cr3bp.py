"""Utilities for the circular restricted three-body problem.

This module implements a small self-contained model of the Sun-Earth CR3BP:
- computes all five Lagrange points
- integrates trajectories near any chosen point
- builds static plots and HTML animations

SciPy is intentionally not required. Root finding and time integration are
implemented locally so the project can run in a minimal Python environment.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

import matplotlib

# Use a non-interactive backend so files can be rendered from the terminal.
matplotlib.use("Agg")
matplotlib.rcParams["animation.embed_limit"] = 256.0
matplotlib.rcParams["figure.dpi"] = 160
matplotlib.rcParams["savefig.dpi"] = 300

from matplotlib import animation
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401


SUN_MASS_KG = 1.9885e30
EARTH_MASS_KG = 5.97219e24
SUN_EARTH_DISTANCE_M = 149_597_870_700.0


@dataclass(frozen=True)
class SystemParameters:
    """Normalized parameters of the CR3BP."""

    name: str
    mu: float
    distance_m: float


@dataclass(frozen=True)
class SimulationConfig:
    """Configuration for one trajectory run."""

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


def sun_earth_system() -> SystemParameters:
    """Return normalized parameters for the Sun-Earth system."""

    mu = EARTH_MASS_KG / (SUN_MASS_KG + EARTH_MASS_KG)
    return SystemParameters(
        name="sun-earth",
        mu=mu,
        distance_m=SUN_EARTH_DISTANCE_M,
    )


def _collinear_equation(x: float, mu: float) -> float:
    """Equation whose roots give L1, L2, L3 on the x-axis."""

    r1 = abs(x + mu)
    r2 = abs(x - (1.0 - mu))
    return x - (1.0 - mu) * (x + mu) / r1**3 - mu * (x - (1.0 - mu)) / r2**3


def _bisect_root(func, left: float, right: float, *, tol: float = 1e-13, max_iter: int = 200) -> float:
    """Simple bisection method for robust root finding."""

    f_left = func(left)
    f_right = func(right)
    if f_left == 0.0:
        return left
    if f_right == 0.0:
        return right
    if f_left * f_right > 0.0:
        raise ValueError(f"Root is not bracketed on [{left}, {right}]")

    for _ in range(max_iter):
        mid = 0.5 * (left + right)
        f_mid = func(mid)
        if abs(f_mid) < tol or abs(right - left) < tol:
            return mid
        if f_left * f_mid < 0.0:
            right = mid
            f_right = f_mid
        else:
            left = mid
            f_left = f_mid
    return 0.5 * (left + right)


def lagrange_points(mu: float) -> dict[str, np.ndarray]:
    """Compute coordinates of all five Lagrange points."""

    x1 = -mu
    x2 = 1.0 - mu
    eps = 1e-6

    l1_x = _bisect_root(lambda x: _collinear_equation(x, mu), x1 + eps, x2 - eps)
    l2_x = _bisect_root(lambda x: _collinear_equation(x, mu), x2 + eps, 2.0)
    l3_x = _bisect_root(lambda x: _collinear_equation(x, mu), -2.0, x1 - eps)

    return {
        "L1": np.array([l1_x, 0.0, 0.0], dtype=float),
        "L2": np.array([l2_x, 0.0, 0.0], dtype=float),
        "L3": np.array([l3_x, 0.0, 0.0], dtype=float),
        "L4": np.array([0.5 - mu, np.sqrt(3.0) / 2.0, 0.0], dtype=float),
        "L5": np.array([0.5 - mu, -np.sqrt(3.0) / 2.0, 0.0], dtype=float),
    }


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


def cr3bp_rhs(state: np.ndarray, mu: float) -> np.ndarray:
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


def integrate_rk4(initial_state: np.ndarray, mu: float, t_max: float, dt: float) -> tuple[np.ndarray, np.ndarray]:
    """Integrate the CR3BP equations with the classical RK4 method."""

    num_steps = int(np.ceil(t_max / dt)) + 1
    times = np.linspace(0.0, dt * (num_steps - 1), num_steps)
    states = np.zeros((num_steps, 6), dtype=float)
    states[0] = initial_state

    for index in range(num_steps - 1):
        current = states[index]
        k1 = cr3bp_rhs(current, mu)
        k2 = cr3bp_rhs(current + 0.5 * dt * k1, mu)
        k3 = cr3bp_rhs(current + 0.5 * dt * k2, mu)
        k4 = cr3bp_rhs(current + dt * k3, mu)
        states[index + 1] = current + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

    return times, states


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


def save_lagrange_points(points: dict[str, np.ndarray], path: Path) -> None:
    """Store coordinates of the five Lagrange points as JSON."""

    payload = {name: coords.tolist() for name, coords in points.items()}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _apply_dark_2d_style(ax) -> None:
    """Apply a dark neon-like style to a 2D axis."""

    ax.set_facecolor("#070b14")
    for spine in ax.spines.values():
        spine.set_color("#4b5568")
    ax.tick_params(colors="#d6e2ff")
    ax.xaxis.label.set_color("#e6f0ff")
    ax.yaxis.label.set_color("#e6f0ff")
    ax.title.set_color("#f6f8ff")
    ax.grid(True, color="#243041", alpha=0.45, linewidth=0.8)


def _apply_dark_3d_style(ax) -> None:
    """Apply a dark style to a 3D axis."""

    ax.set_facecolor("#070b14")
    ax.xaxis.label.set_color("#e6f0ff")
    ax.yaxis.label.set_color("#e6f0ff")
    ax.zaxis.label.set_color("#e6f0ff")
    ax.title.set_color("#f6f8ff")
    ax.tick_params(colors="#d6e2ff")
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.line.set_color("#4b5568")
        axis.pane.set_facecolor((0.08, 0.11, 0.18, 0.7))
        axis.pane.set_edgecolor((0.3, 0.35, 0.42, 1.0))
    ax.grid(True, color="#243041", alpha=0.4)


def plot_system_layout(points: dict[str, np.ndarray], system: SystemParameters, output_path: Path) -> None:
    """Save a dark themed overview plus a zoom near Earth, L1 and L2."""

    fig, (ax_full, ax_zoom) = plt.subplots(1, 2, figsize=(26, 12), facecolor="#05070d")
    fig.suptitle("Система Солнце - Земля и расположение точек Лагранжа", color="#f6f8ff", fontsize=18, y=0.98)

    for ax in (ax_full, ax_zoom):
        _apply_dark_2d_style(ax)
        ax.set_aspect("equal", adjustable="box")
        ax.axhline(0.0, color="#5b6475", linewidth=1.0, linestyle="--", zorder=0)

    ax_full.set_title("Полная схема системы")
    ax_full.set_xlabel("x, безразмерная координата")
    ax_full.set_ylabel("y, безразмерная координата")

    ax_zoom.set_title("Увеличение области около Земли, L1 и L2")
    ax_zoom.set_xlabel("x, безразмерная координата")
    ax_zoom.set_ylabel("y, безразмерная координата")

    # Draw the primaries.
    sun_color = "#ffb000"
    earth_color = "#4ea1ff"
    lagrange_color = "#ff5b5b"
    triangular_color = "#7cff7a"

    for ax in (ax_full, ax_zoom):
        ax.scatter(-system.mu, 0.0, s=460, color=sun_color, edgecolor="#111111", linewidth=1.2, zorder=5)
        ax.scatter(1.0 - system.mu, 0.0, s=130, color=earth_color, edgecolor="#111111", linewidth=1.0, zorder=6)

    ax_full.text(-system.mu - 0.09, 0.04, "Солнце", fontsize=12, weight="bold", color=sun_color)
    ax_full.text(1.0 - system.mu + 0.03, 0.06, "Земля", fontsize=12, weight="bold", color=earth_color)
    ax_zoom.text(1.0 - system.mu + 0.01, 0.006, "Земля", fontsize=11, weight="bold", color=earth_color)

    for name, coords in points.items():
        color = triangular_color if name in {"L4", "L5"} else lagrange_color
        size = 75 if name in {"L4", "L5"} else 62
        ax_full.scatter(coords[0], coords[1], s=size, color=color, edgecolor="#111111", linewidth=0.8, zorder=7)
        if name in {"L1", "L2", "L3", "L4", "L5"}:
            ax_full.text(coords[0] + 0.03, coords[1] + 0.03, name, fontsize=11, weight="bold", color=color)

    for name in ("L1", "L2"):
        coords = points[name]
        ax_zoom.scatter(coords[0], coords[1], s=90, color=lagrange_color, edgecolor="#111111", linewidth=0.8, zorder=7)
        offset = -0.006 if name == "L1" else 0.004
        ax_zoom.text(coords[0] + offset, coords[1] + 0.006, name, fontsize=11, weight="bold", color=lagrange_color)

    ax_zoom.add_patch(
        Circle(
            (1.0 - system.mu, 0.0),
            0.006,
            facecolor=(0.30, 0.63, 1.0, 0.18),
            edgecolor=(0.30, 0.63, 1.0, 0.85),
            linewidth=1.1,
        )
    )

    ax_full.set_xlim(-1.25, 1.25)
    ax_full.set_ylim(-1.05, 1.05)
    ax_zoom.set_xlim(0.975, 1.03)
    ax_zoom.set_ylim(-0.018, 0.018)

    legend_items = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=sun_color, markeredgecolor="#111111", markersize=15, label="Солнце"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=earth_color, markeredgecolor="#111111", markersize=11, label="Земля"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=lagrange_color, markeredgecolor="#111111", markersize=10, label="Коллинеарные точки L1, L2, L3"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=triangular_color, markeredgecolor="#111111", markersize=10, label="Треугольные точки L4, L5"),
        Line2D([0], [0], color="#5b6475", linestyle="--", linewidth=1.2, label="Ось y = 0"),
    ]
    legend = fig.legend(
        handles=legend_items,
        loc="center left",
        bbox_to_anchor=(0.88, 0.5),
        frameon=True,
        facecolor="#0d1220",
        edgecolor="#4b5568",
        fontsize=12,
        title="Обозначения",
        title_fontsize=13,
    )
    for text in legend.get_texts():
        text.set_color("#e6f0ff")
    legend.get_title().set_color("#f6f8ff")

    fig.tight_layout(rect=[0.0, 0.0, 0.86, 0.95], pad=1.5)
    fig.savefig(output_path, dpi=320)
    fig.savefig(output_path.with_suffix(".svg"))
    plt.close(fig)


def plot_trajectory_3d(
    points: dict[str, np.ndarray],
    states: np.ndarray,
    system: SystemParameters,
    config: SimulationConfig,
    output_path: Path,
) -> None:
    """Save a dark themed 3D view of the system and trajectory."""

    fig = plt.figure(figsize=(20, 15), facecolor="#05070d")
    ax = fig.add_subplot(111, projection="3d")
    _apply_dark_3d_style(ax)

    target = points[config.point_name]
    rel_distance = np.sqrt((states[:, 0] - target[0]) ** 2 + (states[:, 1] - target[1]) ** 2 + (states[:, 2] - target[2]) ** 2)

    # Draw a translucent reference plane z=0.
    plane_extent = 0.06 if config.point_name in {"L1", "L2", "L3"} else 0.03
    xx, yy = np.meshgrid(
        np.linspace(target[0] - plane_extent, target[0] + plane_extent, 2),
        np.linspace(target[1] - plane_extent, target[1] + plane_extent, 2),
    )
    zz = np.zeros_like(xx)
    ax.plot_surface(xx, yy, zz, color="#8ba3c7", alpha=0.12, linewidth=0)

    # Plot the trajectory with a time gradient.
    colors = plt.cm.plasma(np.linspace(0.1, 0.95, len(states) - 1))
    for i in range(len(states) - 1):
        ax.plot(
            states[i : i + 2, 0],
            states[i : i + 2, 1],
            states[i : i + 2, 2],
            color=colors[i],
            linewidth=2.0,
            alpha=0.95,
        )

    ax.scatter(target[0], target[1], target[2], s=130, color="#ff5b5b", edgecolor="black", linewidth=0.8)
    ax.text(target[0], target[1], target[2] + 0.003, config.point_name, color="#ff5b5b", fontsize=12, weight="bold")

    ax.scatter(states[0, 0], states[0, 1], states[0, 2], s=90, color="#23d160", edgecolor="black", linewidth=0.7)
    ax.text(states[0, 0], states[0, 1], states[0, 2] - 0.004, "старт", color="#23d160", fontsize=11, weight="bold")
    ax.scatter(states[-1, 0], states[-1, 1], states[-1, 2], s=90, color="#ff7b00", edgecolor="black", linewidth=0.7)
    ax.text(states[-1, 0], states[-1, 1], states[-1, 2] + 0.003, "финиш", color="#ff7b00", fontsize=11, weight="bold")

    # Mark Sun and Earth for orientation.
    ax.scatter(-system.mu, 0.0, 0.0, s=320, color="#ffb000", edgecolor="black", linewidth=0.9)
    ax.scatter(1.0 - system.mu, 0.0, 0.0, s=120, color="#4ea1ff", edgecolor="black", linewidth=0.9)
    ax.text(-system.mu, 0.0, 0.006, "Солнце", color="#ffb000", fontsize=11, weight="bold")
    ax.text(1.0 - system.mu, 0.0, 0.006, "Земля", color="#4ea1ff", fontsize=11, weight="bold")

    behavior = (
        "Неустойчивый случай: траектория уходит от точки"
        if config.point_name in {"L1", "L2", "L3"}
        else "Устойчивый случай: движение остаётся рядом"
    )
    ax.set_title(
        f"3D-вид траектории около {config.point_name}\n"
        f"{behavior}; max r = {rel_distance.max():.4f}",
        pad=16,
    )
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")

    radius = max(np.max(np.abs(states[:, 0] - target[0])), np.max(np.abs(states[:, 1] - target[1])), 0.02) * 1.25
    ax.set_xlim(target[0] - radius, target[0] + radius)
    ax.set_ylim(target[1] - radius, target[1] + radius)
    ax.set_zlim(-radius * 0.6, radius * 0.6)
    ax.view_init(elev=28, azim=-58)

    legend_items = [
        Line2D([0], [0], color="#ffb000", marker="o", linestyle="None", markeredgecolor="black", markersize=13, label="Солнце"),
        Line2D([0], [0], color="#4ea1ff", marker="o", linestyle="None", markeredgecolor="black", markersize=11, label="Земля"),
        Line2D([0], [0], color="#ff5b5b", marker="o", linestyle="None", markeredgecolor="black", markersize=11, label=f"Точка {config.point_name}"),
        Line2D([0], [0], color="#23d160", marker="o", linestyle="None", markeredgecolor="black", markersize=11, label="Начальная точка"),
        Line2D([0], [0], color="#ff7b00", marker="o", linestyle="None", markeredgecolor="black", markersize=11, label="Конец траектории"),
        Line2D([0], [0], color="#d28cff", linewidth=2.5, label="Траектория движения"),
    ]
    legend = fig.legend(
        handles=legend_items,
        loc="center left",
        bbox_to_anchor=(0.86, 0.52),
        frameon=True,
        facecolor="#0d1220",
        edgecolor="#4b5568",
        fontsize=12,
        title="Обозначения",
        title_fontsize=13,
    )
    for text in legend.get_texts():
        text.set_color("#e6f0ff")
    legend.get_title().set_color("#f6f8ff")

    fig.tight_layout(rect=[0.0, 0.0, 0.84, 1.0], pad=1.5)
    fig.savefig(output_path, dpi=320)
    fig.savefig(output_path.with_suffix(".svg"))
    plt.close(fig)


def _time_colored_line(ax, x: np.ndarray, y: np.ndarray) -> None:
    """Draw a line whose color changes with time to show direction of motion."""

    points = np.column_stack([x, y]).reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    colors = np.linspace(0.0, 1.0, len(segments))
    collection = LineCollection(segments, cmap="viridis", linewidth=2.2)
    collection.set_array(colors)
    ax.add_collection(collection)


def plot_trajectory(
    points: dict[str, np.ndarray],
    states: np.ndarray,
    system: SystemParameters,
    config: SimulationConfig,
    output_path: Path,
) -> None:
    """Save a three-panel plot with geometry and deviation from the Lagrange point."""

    target = points[config.point_name]
    start = states[0]
    end = states[-1]

    dx_rel = states[:, 0] - target[0]
    dy_rel = states[:, 1] - target[1]
    rel_distance = np.sqrt(dx_rel**2 + dy_rel**2)

    fig, axes = plt.subplots(1, 3, figsize=(34, 12), facecolor="#05070d")
    ax_global, ax_local, ax_distance = axes
    for ax in axes:
        _apply_dark_2d_style(ax)

    # Global system view.
    ax_global.set_title(f"Общий вид около {config.point_name}")
    ax_global.set_xlabel("x, безразмерная координата")
    ax_global.set_ylabel("y, безразмерная координата")
    ax_global.set_aspect("equal", adjustable="box")
    ax_global.axhline(0.0, color="#8893a8", linewidth=1.0, linestyle="--", zorder=0)
    ax_global.scatter(-system.mu, 0.0, s=220, color="#f4a300", edgecolor="black", linewidth=0.8, zorder=3)
    ax_global.scatter(1.0 - system.mu, 0.0, s=90, color="#2f8fdd", edgecolor="black", linewidth=0.8, zorder=3)
    ax_global.text(-system.mu - 0.09, 0.03, "Солнце", fontsize=10, weight="bold")
    ax_global.text(1.0 - system.mu + 0.02, 0.03, "Земля", fontsize=10, weight="bold")

    for name, coords in points.items():
        color = "#ff5b5b" if name == config.point_name else "#202020"
        size = 130 if name == config.point_name else 50
        ax_global.scatter(coords[0], coords[1], s=size, color=color, edgecolor="black", linewidth=0.5, zorder=4)
        ax_global.text(coords[0] + 0.02, coords[1] + 0.02, name, fontsize=15, weight="bold", color=color)

    ax_global.plot(states[:, 0], states[:, 1], color="#38a3ff", linewidth=2.6, alpha=0.95, zorder=2)
    ax_global.scatter(start[0], start[1], s=120, color="#23d160", edgecolor="black", linewidth=0.8, zorder=5)
    ax_global.scatter(end[0], end[1], s=120, color="#ff7b00", edgecolor="black", linewidth=0.8, zorder=5)
    ax_global.text(
        start[0] + 0.012,
        start[1] - 0.035,
        f"начальная точка\nрядом с {config.point_name}",
        fontsize=13,
        weight="bold",
        color="#23d160",
    )
    ax_global.text(end[0] + 0.012, end[1] + 0.02, "положение в конце", fontsize=13, weight="bold", color="#ff7b00")

    x_center = 0.5 * (states[:, 0].min() + states[:, 0].max())
    y_center = 0.5 * (states[:, 1].min() + states[:, 1].max())
    x_radius = max(np.ptp(states[:, 0]) * 0.7, 0.08)
    y_radius = max(np.ptp(states[:, 1]) * 0.7, 0.08)
    ax_global.set_xlim(x_center - x_radius, x_center + x_radius)
    ax_global.set_ylim(y_center - y_radius, y_center + y_radius)

    # Local view in coordinates relative to the chosen point.
    ax_local.set_title(f"Локальный вид относительно {config.point_name}")
    ax_local.set_xlabel(r"$\Delta x = x - x_{L}$")
    ax_local.set_ylabel(r"$\Delta y = y - y_{L}$")
    ax_local.set_aspect("equal", adjustable="box")
    ax_local.axhline(0.0, color="#c8c8c8", linewidth=1.0)
    ax_local.axvline(0.0, color="#c8c8c8", linewidth=1.0)

    _time_colored_line(ax_local, dx_rel, dy_rel)
    ax_local.scatter(0.0, 0.0, s=190, color="#ff5b5b", edgecolor="black", linewidth=0.8, zorder=5)
    ax_local.scatter(dx_rel[0], dy_rel[0], s=120, color="#23d160", edgecolor="black", linewidth=0.8, zorder=5)
    ax_local.scatter(dx_rel[-1], dy_rel[-1], s=120, color="#ff7b00", edgecolor="black", linewidth=0.8, zorder=5)
    ax_local.text(0.004, 0.004, f"сама точка {config.point_name}", fontsize=14, weight="bold", color="#ff5b5b")
    ax_local.text(dx_rel[0] + 0.002, dy_rel[0] - 0.004, "стартовое положение", fontsize=13, weight="bold", color="#23d160")
    ax_local.text(dx_rel[-1] + 0.002, dy_rel[-1] + 0.002, "конец траектории", fontsize=13, weight="bold", color="#ff7b00")

    local_radius = max(np.max(np.abs(dx_rel)), np.max(np.abs(dy_rel)), 0.01) * 1.15
    ax_local.set_xlim(-local_radius, local_radius)
    ax_local.set_ylim(-local_radius, local_radius)

    # Distance-to-point view.
    ax_distance.set_title(f"Как меняется расстояние до {config.point_name} со временем")
    ax_distance.set_xlabel("t, безразмерное время")
    ax_distance.set_ylabel(r"$r(t) = \sqrt{(\Delta x)^2 + (\Delta y)^2}$")
    ax_distance.plot(
        np.arange(len(rel_distance)) * config.dt,
        rel_distance,
        color="#ff4d6d" if config.point_name in {"L1", "L2", "L3"} else "#7CFF7A",
        linewidth=2.6,
    )
    ax_distance.scatter([0.0], [rel_distance[0]], s=55, color="#12a150", edgecolor="black", linewidth=0.6, zorder=5)
    ax_distance.scatter(
        [(len(rel_distance) - 1) * config.dt],
        [rel_distance[-1]],
        s=55,
        color="#ff6b00",
        edgecolor="black",
        linewidth=0.6,
        zorder=5,
    )
    max_idx = int(np.argmax(rel_distance))
    ax_distance.scatter(
        [max_idx * config.dt],
        [rel_distance[max_idx]],
        s=65,
        color="#ffe066",
        edgecolor="black",
        linewidth=0.6,
        zorder=5,
    )
    ax_distance.text(0.02 * config.t_max, rel_distance[0] + 0.0003, "старт", color="#12a150", fontsize=9, weight="bold")
    ax_distance.text(
        max_idx * config.dt,
        rel_distance[max_idx] + 0.0005,
        f"макс = {rel_distance[max_idx]:.4f}",
        color="#ffe066",
        fontsize=9,
        weight="bold",
    )
    if config.point_name in {"L1", "L2", "L3"}:
        ax_distance.text(
            0.52 * config.t_max,
            0.82 * rel_distance.max(),
            "Неустойчивость видна здесь:\nрасстояние до точки со временем\nстановится заметно больше",
            color="#ff9ab1",
            fontsize=13,
            weight="bold",
        )
    else:
        ax_distance.text(
            0.45 * config.t_max,
            0.75 * rel_distance.max(),
            "Устойчивость видна здесь:\nтраектория отклоняется,\nно остаётся рядом с точкой",
            color="#9dffae",
            fontsize=13,
            weight="bold",
        )
    ax_distance.set_xlim(0.0, (len(rel_distance) - 1) * config.dt)
    ax_distance.set_ylim(0.0, rel_distance.max() * 1.18 if rel_distance.max() > 0 else 1.0)

    behavior = (
        "неустойчивый случай: траектория уходит от точки"
        if config.point_name in {"L1", "L2", "L3"}
        else "устойчивый случай: движение остаётся рядом"
    )
    fig.suptitle(
        f"Траектория в задаче Солнце - Земля около {config.point_name}\n"
        f"Начальная точка задана рядом с {config.point_name}; {behavior}; максимальное удаление = {rel_distance.max():.4f}",
        fontsize=20,
        y=0.98,
    )
    trajectory_color = "#38a3ff"
    distance_color = "#ff4d6d" if config.point_name in {"L1", "L2", "L3"} else "#7CFF7A"
    legend_items = [
        Line2D([0], [0], color=trajectory_color, linewidth=3.2, label="Траектория в системе координат"),
        Line2D([0], [0], color="#7c5cff", linewidth=3.2, label="Траектория в локальном окне"),
        Line2D([0], [0], color=distance_color, linewidth=3.2, label="Отклонение от точки L во времени"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#ff5b5b", markeredgecolor="black", markersize=13, label=f"Выбранная точка {config.point_name}"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#23d160", markeredgecolor="black", markersize=12, label="Начальная точка"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#ff7b00", markeredgecolor="black", markersize=12, label="Конец траектории"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#f4a300", markeredgecolor="black", markersize=14, label="Солнце"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#2f8fdd", markeredgecolor="black", markersize=12, label="Земля"),
    ]
    legend = fig.legend(
        handles=legend_items,
        loc="center left",
        bbox_to_anchor=(0.88, 0.5),
        frameon=True,
        facecolor="#0d1220",
        edgecolor="#4b5568",
        fontsize=13,
        title="Что обозначено на рисунке",
        title_fontsize=14,
    )
    for text in legend.get_texts():
        text.set_color("#e6f0ff")
    legend.get_title().set_color("#f6f8ff")

    fig.tight_layout(rect=[0.0, 0.0, 0.86, 0.94], pad=1.6)
    fig.savefig(output_path, dpi=340)
    fig.savefig(output_path.with_suffix(".svg"))
    plt.close(fig)


def save_animation_html(
    points: dict[str, np.ndarray],
    states: np.ndarray,
    system: SystemParameters,
    config: SimulationConfig,
    output_path: Path,
) -> None:
    """Save an interactive HTML animation that can be opened locally."""

    sampled_states = states[:: max(1, config.sample_stride)]

    fig, ax = plt.subplots(figsize=(12, 12), facecolor="#05070d")
    _apply_dark_2d_style(ax)
    ax.set_title(f"Анимация траектории около {config.point_name}", fontsize=20)
    ax.set_xlabel("x, безразмерная координата")
    ax.set_ylabel("y, безразмерная координата")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.35)

    ax.scatter(
        [-system.mu, 1.0 - system.mu],
        [0.0, 0.0],
        s=[340, 120],
        color=["#f4a300", "#2f8fdd"],
        edgecolor="black",
        linewidth=0.8,
        zorder=4,
    )
    for name, coords in points.items():
        color = "#ff5b5b" if name == config.point_name else "#d6e2ff"
        size = 90 if name == config.point_name else 46
        ax.scatter(coords[0], coords[1], s=size, color=color, edgecolor="black", linewidth=0.6, zorder=5)
        ax.text(coords[0] + 0.012, coords[1] + 0.012, name, fontsize=12, color=color, weight="bold")

    x_margin = 0.08
    y_margin = 0.08
    ax.set_xlim(sampled_states[:, 0].min() - x_margin, sampled_states[:, 0].max() + x_margin)
    ax.set_ylim(sampled_states[:, 1].min() - y_margin, sampled_states[:, 1].max() + y_margin)

    (trail_line,) = ax.plot([], [], color="#59b7ff", linewidth=2.8)
    (body_point,) = ax.plot([], [], "o", color="#ff6b57", markersize=9)

    def _init():
        trail_line.set_data([], [])
        body_point.set_data([], [])
        return trail_line, body_point

    def _update(frame_index: int):
        trail_line.set_data(sampled_states[: frame_index + 1, 0], sampled_states[: frame_index + 1, 1])
        body_point.set_data([sampled_states[frame_index, 0]], [sampled_states[frame_index, 1]])
        return trail_line, body_point

    anim = animation.FuncAnimation(
        fig,
        _update,
        init_func=_init,
        frames=len(sampled_states),
        interval=55,
        blit=True,
    )

    html = anim.to_jshtml()
    output_path.write_text(html, encoding="utf-8")
    plt.close(fig)


def simulation_summary(
    system: SystemParameters,
    config: SimulationConfig,
    points: dict[str, np.ndarray],
    initial_state: np.ndarray,
) -> dict[str, object]:
    """Create a small metadata dictionary for one run."""

    return {
        "system": system.name,
        "mu": system.mu,
        "point_name": config.point_name,
        "point_coordinates": points[config.point_name].tolist(),
        "initial_state": initial_state.tolist(),
        "t_max": config.t_max,
        "dt": config.dt,
        "sample_stride": config.sample_stride,
    }


def save_summary(summary: dict[str, object], path: Path) -> None:
    """Store run metadata as JSON."""

    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
