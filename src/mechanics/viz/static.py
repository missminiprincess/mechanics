"""Static matplotlib plots for report-ready outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Circle

from mechanics.core.models import LagrangePointMap, SimulationResult, SystemParameters
from mechanics.viz.styles import apply_dark_2d_style, apply_dark_3d_style


def plot_system_layout(
    points: LagrangePointMap, system: SystemParameters, output_path: Path
) -> None:
    """Save an overview of the Sun-Earth system and all Lagrange points."""

    fig, (ax_full, ax_zoom) = plt.subplots(1, 2, figsize=(24, 11), facecolor="#05070d")
    fig.suptitle(
        "Система Солнце - Земля и расположение точек Лагранжа", color="#f6f8ff", fontsize=18, y=0.98
    )

    for ax in (ax_full, ax_zoom):
        apply_dark_2d_style(ax)
        ax.set_aspect("equal", adjustable="box")
        ax.axhline(0.0, color="#5b6475", linewidth=1.0, linestyle="--", zorder=0)

    ax_full.set_title("Полная схема системы")
    ax_full.set_xlabel("x, безразмерная координата")
    ax_full.set_ylabel("y, безразмерная координата")
    ax_zoom.set_title("Увеличение области около Земли, L1 и L2")
    ax_zoom.set_xlabel("x, безразмерная координата")
    ax_zoom.set_ylabel("y, безразмерная координата")

    sun_color = "#ffb000"
    earth_color = "#4ea1ff"
    lagrange_color = "#ff5b5b"
    triangular_color = "#7cff7a"

    for ax in (ax_full, ax_zoom):
        ax.scatter(
            -system.mu, 0.0, s=430, color=sun_color, edgecolor="#111111", linewidth=1.2, zorder=5
        )
        ax.scatter(
            1.0 - system.mu,
            0.0,
            s=120,
            color=earth_color,
            edgecolor="#111111",
            linewidth=1.0,
            zorder=6,
        )

    ax_full.text(-system.mu - 0.09, 0.04, "Солнце", fontsize=12, weight="bold", color=sun_color)
    ax_full.text(
        1.0 - system.mu + 0.03, 0.06, "Земля", fontsize=12, weight="bold", color=earth_color
    )
    ax_zoom.text(
        1.0 - system.mu + 0.01, 0.006, "Земля", fontsize=11, weight="bold", color=earth_color
    )

    for name, coords in points.items():
        color = triangular_color if name in {"L4", "L5"} else lagrange_color
        size = 75 if name in {"L4", "L5"} else 62
        ax_full.scatter(
            coords[0], coords[1], s=size, color=color, edgecolor="#111111", linewidth=0.8, zorder=7
        )
        ax_full.text(
            coords[0] + 0.03, coords[1] + 0.03, name, fontsize=11, weight="bold", color=color
        )

    for name in ("L1", "L2"):
        coords = points[name]
        ax_zoom.scatter(
            coords[0],
            coords[1],
            s=90,
            color=lagrange_color,
            edgecolor="#111111",
            linewidth=0.8,
            zorder=7,
        )
        offset = -0.006 if name == "L1" else 0.004
        ax_zoom.text(
            coords[0] + offset,
            coords[1] + 0.006,
            name,
            fontsize=11,
            weight="bold",
            color=lagrange_color,
        )

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
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=sun_color,
            markeredgecolor="#111111",
            markersize=15,
            label="Солнце",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=earth_color,
            markeredgecolor="#111111",
            markersize=11,
            label="Земля",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=lagrange_color,
            markeredgecolor="#111111",
            markersize=10,
            label="Коллинеарные точки L1, L2, L3",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=triangular_color,
            markeredgecolor="#111111",
            markersize=10,
            label="Треугольные точки L4, L5",
        ),
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

    fig.tight_layout(rect=(0.0, 0.0, 0.86, 0.95), pad=1.5)
    fig.savefig(output_path)
    fig.savefig(output_path.with_suffix(".svg"))
    plt.close(fig)


def _time_colored_line(ax: Any, x: np.ndarray, y: np.ndarray) -> None:
    """Draw a line whose color changes with time."""

    points = np.column_stack([x, y]).reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    collection = LineCollection(segments, cmap="viridis", linewidth=2.2)
    collection.set_array(np.linspace(0.0, 1.0, len(segments)))
    ax.add_collection(collection)


def plot_trajectory(result: SimulationResult, output_path: Path) -> None:
    """Save a three-panel trajectory figure."""

    system = result.system
    config = result.config
    states = result.states
    points = result.points
    target = result.point

    dx_rel = states[:, 0] - target[0]
    dy_rel = states[:, 1] - target[1]
    rel_distance = np.hypot(dx_rel, dy_rel)

    fig, axes = plt.subplots(1, 3, figsize=(30, 11), facecolor="#05070d")
    ax_global, ax_local, ax_distance = axes
    for ax in axes:
        apply_dark_2d_style(ax)

    ax_global.set_title(f"Общий вид около {config.point_name}")
    ax_global.set_xlabel("x, безразмерная координата")
    ax_global.set_ylabel("y, безразмерная координата")
    ax_global.set_aspect("equal", adjustable="box")
    ax_global.axhline(0.0, color="#8893a8", linewidth=1.0, linestyle="--", zorder=0)
    ax_global.scatter(
        -system.mu, 0.0, s=220, color="#f4a300", edgecolor="black", linewidth=0.8, zorder=3
    )
    ax_global.scatter(
        1.0 - system.mu, 0.0, s=90, color="#2f8fdd", edgecolor="black", linewidth=0.8, zorder=3
    )
    ax_global.text(-system.mu - 0.09, 0.03, "Солнце", fontsize=10, weight="bold")
    ax_global.text(1.0 - system.mu + 0.02, 0.03, "Земля", fontsize=10, weight="bold")

    for name, coords in points.items():
        color = "#ff5b5b" if name == config.point_name else "#202020"
        size = 130 if name == config.point_name else 50
        ax_global.scatter(
            coords[0], coords[1], s=size, color=color, edgecolor="black", linewidth=0.5, zorder=4
        )
        ax_global.text(
            coords[0] + 0.02, coords[1] + 0.02, name, fontsize=15, weight="bold", color=color
        )

    ax_global.plot(states[:, 0], states[:, 1], color="#38a3ff", linewidth=2.6, alpha=0.95, zorder=2)
    ax_global.scatter(
        states[0, 0],
        states[0, 1],
        s=120,
        color="#23d160",
        edgecolor="black",
        linewidth=0.8,
        zorder=5,
    )
    ax_global.scatter(
        states[-1, 0],
        states[-1, 1],
        s=120,
        color="#ff7b00",
        edgecolor="black",
        linewidth=0.8,
        zorder=5,
    )

    x_center = 0.5 * (states[:, 0].min() + states[:, 0].max())
    y_center = 0.5 * (states[:, 1].min() + states[:, 1].max())
    ax_global.set_xlim(
        x_center - max(np.ptp(states[:, 0]) * 0.7, 0.08),
        x_center + max(np.ptp(states[:, 0]) * 0.7, 0.08),
    )
    ax_global.set_ylim(
        y_center - max(np.ptp(states[:, 1]) * 0.7, 0.08),
        y_center + max(np.ptp(states[:, 1]) * 0.7, 0.08),
    )

    ax_local.set_title(f"Локальный вид относительно {config.point_name}")
    ax_local.set_xlabel(r"$\Delta x = x - x_{L}$")
    ax_local.set_ylabel(r"$\Delta y = y - y_{L}$")
    ax_local.set_aspect("equal", adjustable="box")
    ax_local.axhline(0.0, color="#c8c8c8", linewidth=1.0)
    ax_local.axvline(0.0, color="#c8c8c8", linewidth=1.0)
    _time_colored_line(ax_local, dx_rel, dy_rel)
    ax_local.scatter(0.0, 0.0, s=190, color="#ff5b5b", edgecolor="black", linewidth=0.8, zorder=5)
    ax_local.scatter(
        dx_rel[0], dy_rel[0], s=120, color="#23d160", edgecolor="black", linewidth=0.8, zorder=5
    )
    ax_local.scatter(
        dx_rel[-1], dy_rel[-1], s=120, color="#ff7b00", edgecolor="black", linewidth=0.8, zorder=5
    )

    local_radius = max(np.max(np.abs(dx_rel)), np.max(np.abs(dy_rel)), 0.01) * 1.15
    ax_local.set_xlim(-local_radius, local_radius)
    ax_local.set_ylim(-local_radius, local_radius)

    distance_color = "#ff4d6d" if config.point_name in {"L1", "L2", "L3"} else "#7cff7a"
    ax_distance.set_title(f"Расстояние до {config.point_name} во времени")
    ax_distance.set_xlabel("t, безразмерное время")
    ax_distance.set_ylabel(r"$r(t) = \sqrt{(\Delta x)^2 + (\Delta y)^2}$")
    ax_distance.plot(result.times, rel_distance, color=distance_color, linewidth=2.6)
    ax_distance.set_xlim(0.0, float(result.times[-1]))
    ax_distance.set_ylim(0.0, rel_distance.max() * 1.18 if rel_distance.max() > 0 else 1.0)

    behavior = (
        "неустойчивый случай: траектория уходит от точки"
        if config.point_name in {"L1", "L2", "L3"}
        else "устойчивый случай: движение остаётся рядом"
    )
    fig.suptitle(
        (
            f"Траектория около {config.point_name}: {behavior}; "
            f"максимальное удаление = {rel_distance.max():.4f}"
        ),
        color="#f6f8ff",
        fontsize=18,
        y=0.98,
    )
    fig.subplots_adjust(left=0.06, right=0.98, bottom=0.1, top=0.88, wspace=0.2)
    fig.savefig(output_path)
    fig.savefig(output_path.with_suffix(".svg"))
    plt.close(fig)


def plot_trajectory_3d(result: SimulationResult, output_path: Path) -> None:
    """Save a 3D trajectory figure."""

    fig = plt.figure(figsize=(16, 12), facecolor="#05070d")
    ax: Any = fig.add_subplot(111, projection="3d")
    apply_dark_3d_style(ax)

    states = result.states
    target = result.point
    rel_distance = np.linalg.norm(result.rel_states, axis=1)

    plane_extent = 0.06 if result.point_name in {"L1", "L2", "L3"} else 0.03
    xx, yy = np.meshgrid(
        np.linspace(target[0] - plane_extent, target[0] + plane_extent, 2),
        np.linspace(target[1] - plane_extent, target[1] + plane_extent, 2),
    )
    ax.plot_surface(xx, yy, np.zeros_like(xx), color="#8ba3c7", alpha=0.12, linewidth=0)

    colors = plt.get_cmap("plasma")(np.linspace(0.1, 0.95, len(states) - 1))
    for i in range(len(states) - 1):
        ax.plot(
            states[i : i + 2, 0],
            states[i : i + 2, 1],
            states[i : i + 2, 2],
            color=colors[i],
            linewidth=2.0,
        )

    ax.scatter(
        target[0], target[1], target[2], s=130, color="#ff5b5b", edgecolor="black", linewidth=0.8
    )
    ax.scatter(
        states[0, 0],
        states[0, 1],
        states[0, 2],
        s=90,
        color="#23d160",
        edgecolor="black",
        linewidth=0.7,
    )
    ax.scatter(
        states[-1, 0],
        states[-1, 1],
        states[-1, 2],
        s=90,
        color="#ff7b00",
        edgecolor="black",
        linewidth=0.7,
    )
    ax.scatter(
        -result.system.mu, 0.0, 0.0, s=320, color="#ffb000", edgecolor="black", linewidth=0.9
    )
    ax.scatter(
        1.0 - result.system.mu, 0.0, 0.0, s=120, color="#4ea1ff", edgecolor="black", linewidth=0.9
    )

    behavior = (
        "Неустойчивый случай: траектория уходит от точки"
        if result.point_name in {"L1", "L2", "L3"}
        else "Устойчивый случай: движение остаётся рядом"
    )
    ax.set_title(
        (
            f"3D-вид траектории около {result.point_name}\n"
            f"{behavior}; max r = {rel_distance.max():.4f}"
        ),
        pad=16,
    )
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")

    radius = (
        max(
            np.max(np.abs(states[:, 0] - target[0])), np.max(np.abs(states[:, 1] - target[1])), 0.02
        )
        * 1.25
    )
    ax.set_xlim(target[0] - radius, target[0] + radius)
    ax.set_ylim(target[1] - radius, target[1] + radius)
    ax.set_zlim(-radius * 0.6, radius * 0.6)
    ax.view_init(elev=28, azim=-58)

    fig.tight_layout(pad=1.5)
    fig.savefig(output_path)
    fig.savefig(output_path.with_suffix(".svg"))
    plt.close(fig)
