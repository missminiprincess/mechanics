"""Interactive Plotly visualizations."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import plotly.graph_objects as go  # type: ignore[import-untyped]
from plotly.subplots import make_subplots  # type: ignore[import-untyped]

from mechanics.core.models import SimulationResult


def build_dashboard(result: SimulationResult) -> go.Figure:
    """Build one interactive dashboard for a simulation result."""

    states = result.states
    rel = result.rel_states
    fig = make_subplots(
        rows=1,
        cols=3,
        specs=[[{"type": "xy"}, {"type": "scene"}, {"type": "xy"}]],
        subplot_titles=(
            f"Траектория в системе координат около {result.point_name}",
            f"Локальный 3D-вид около {result.point_name}",
            f"Расстояние до {result.point_name} во времени",
        ),
        column_widths=[0.34, 0.34, 0.32],
        horizontal_spacing=0.06,
    )

    fig.add_trace(
        go.Scatter(
            x=states[:, 0],
            y=states[:, 1],
            mode="lines",
            line={"color": "#38a3ff", "width": 3},
            name="Траектория",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=[-result.system.mu, 1.0 - result.system.mu],
            y=[0.0, 0.0],
            mode="markers+text",
            marker={"size": [18, 12], "color": ["#ffb000", "#4ea1ff"]},
            text=["Солнце", "Земля"],
            textposition="top center",
            name="Тела системы",
        ),
        row=1,
        col=1,
    )
    for name, coords in result.points.items():
        color = "#ff5b5b" if name == result.point_name else "#8f9bb3"
        fig.add_trace(
            go.Scatter(
                x=[coords[0]],
                y=[coords[1]],
                mode="markers+text",
                marker={"size": 10 if name == result.point_name else 7, "color": color},
                text=[name],
                textposition="top center",
                name=name,
                showlegend=False,
            ),
            row=1,
            col=1,
        )

    fig.add_trace(
        go.Scatter3d(
            x=rel[:, 0],
            y=rel[:, 1],
            z=rel[:, 2],
            mode="lines",
            line={"color": "#d28cff", "width": 5},
            name="Локальная 3D-траектория",
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter3d(
            x=[0.0],
            y=[0.0],
            z=[0.0],
            mode="markers",
            marker={"size": 7, "color": "#ff5b5b"},
            name=result.point_name,
            showlegend=False,
        ),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Scatter(
            x=result.times,
            y=result.rel_distance_xy,
            mode="lines",
            line={
                "color": "#ff4d6d" if result.point_name in {"L1", "L2", "L3"} else "#7cff7a",
                "width": 3,
            },
            name="Отклонение",
        ),
        row=1,
        col=3,
    )

    fig.update_xaxes(title_text="x", row=1, col=1, gridcolor="#243041", zerolinecolor="#4b5568")
    fig.update_yaxes(title_text="y", row=1, col=1, gridcolor="#243041", zerolinecolor="#4b5568")
    fig.update_xaxes(title_text="t", row=1, col=3, gridcolor="#243041", zerolinecolor="#4b5568")
    fig.update_yaxes(title_text="r(t)", row=1, col=3, gridcolor="#243041", zerolinecolor="#4b5568")

    radius = max(float(np.max(np.abs(rel[:, 0]))), float(np.max(np.abs(rel[:, 1]))), 0.01) * 1.35
    z_radius = max(float(np.max(np.abs(rel[:, 2]))), radius * 0.5)
    fig.update_layout(
        title=(
            f"Интерактивная визуализация около {result.point_name}: "
            f"max r = {float(result.rel_distance_xy.max()):.4f}"
        ),
        template="plotly_dark",
        paper_bgcolor="#05070d",
        plot_bgcolor="#070b14",
        scene={
            "xaxis": {"title": "Δx", "backgroundcolor": "#111827", "gridcolor": "#4b5568"},
            "yaxis": {"title": "Δy", "backgroundcolor": "#111827", "gridcolor": "#4b5568"},
            "zaxis": {"title": "Δz", "backgroundcolor": "#111827", "gridcolor": "#4b5568"},
            "camera": {"eye": {"x": 1.5, "y": -1.8, "z": 1.0}},
            "aspectmode": "manual",
            "aspectratio": {"x": 1.0, "y": 1.0, "z": 0.7},
            "xaxis_range": [-radius, radius],
            "yaxis_range": [-radius, radius],
            "zaxis_range": [-z_radius, z_radius],
        },
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.12, "xanchor": "left", "x": 0.0},
        margin={"l": 30, "r": 30, "t": 70, "b": 60},
    )
    return fig


def save_dashboard(result: SimulationResult, output_path: Path) -> None:
    """Write one interactive dashboard to HTML."""

    figure = build_dashboard(result)
    figure.write_html(output_path, include_plotlyjs="cdn", full_html=True)
