"""Shared style helpers for static plots."""

from typing import Any

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["figure.dpi"] = 160
matplotlib.rcParams["savefig.dpi"] = 240


def apply_dark_2d_style(ax: Any) -> None:
    """Apply a dark style to a 2D axis."""

    ax.set_facecolor("#070b14")
    for spine in ax.spines.values():
        spine.set_color("#4b5568")
    ax.tick_params(colors="#d6e2ff")
    ax.xaxis.label.set_color("#e6f0ff")
    ax.yaxis.label.set_color("#e6f0ff")
    ax.title.set_color("#f6f8ff")
    ax.grid(True, color="#243041", alpha=0.45, linewidth=0.8)


def apply_dark_3d_style(ax: Any) -> None:
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
