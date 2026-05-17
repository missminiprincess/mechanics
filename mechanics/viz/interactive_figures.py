"""Plotly figures for interactive CR3BP dashboards."""

import numpy as np
import plotly.graph_objects as go  # type: ignore[import-untyped]

from mechanics.core.models import SimulationResult
from mechanics.viz.plotly_styles import (
    AXIS_COLOR,
    DISTANCE_STABLE_COLOR,
    DISTANCE_UNSTABLE_COLOR,
    END_COLOR,
    LOCAL_3D_COLOR,
    MUTED_COLOR,
    START_COLOR,
    TARGET_COLOR,
    TRAJECTORY_COLOR,
    base_layout,
    style_xy_axes,
)


def sample_indices(result: SimulationResult) -> np.ndarray:
    """Return stable sample indices for interactive outputs."""

    stride = max(1, result.config.sample_stride)
    indices = np.arange(0, len(result.times), stride, dtype=int)
    if indices[-1] != len(result.times) - 1:
        indices = np.append(indices, len(result.times) - 1)
    return indices


def local_radius(rel: np.ndarray) -> float:
    """Return a readable symmetric radius around the selected Lagrange point."""

    return max(float(np.max(np.abs(rel[:, 0]))), float(np.max(np.abs(rel[:, 1]))), 0.001) * 1.18


def build_local_2d(result: SimulationResult, sample: np.ndarray) -> go.Figure:
    """Build the main local 2D trajectory figure."""

    rel = result.rel_states[sample]
    times = result.times[sample]
    radius = local_radius(result.rel_states)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=rel[:, 0],
            y=rel[:, 1],
            customdata=times,
            mode="lines",
            line={"color": TRAJECTORY_COLOR, "width": 3},
            name="Траектория",
            hovertemplate="t=%{customdata:.3f}<br>Δx=%{x:.6f}<br>Δy=%{y:.6f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[0.0],
            y=[0.0],
            mode="markers+text",
            marker={"size": 13, "color": TARGET_COLOR},
            text=[result.point_name],
            textposition="top center",
            name=result.point_name,
            hovertemplate=f"{result.point_name}<br>Δx=0<br>Δy=0<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[result.rel_states[0, 0], result.rel_states[-1, 0]],
            y=[result.rel_states[0, 1], result.rel_states[-1, 1]],
            mode="markers+text",
            marker={"size": [11, 11], "color": [START_COLOR, END_COLOR]},
            text=["start", "end"],
            textposition="bottom center",
            name="Начало/конец",
            hovertemplate="Δx=%{x:.6f}<br>Δy=%{y:.6f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[rel[0, 0]],
            y=[rel[0, 1]],
            mode="markers",
            marker={
                "size": 12,
                "color": "#ffffff",
                "line": {"color": TRAJECTORY_COLOR, "width": 2},
            },
            name="Текущее положение",
            hovertemplate="t=%{customdata:.3f}<br>Δx=%{x:.6f}<br>Δy=%{y:.6f}<extra></extra>",
            customdata=[times[0]],
        )
    )
    fig.frames = [
        go.Frame(
            data=[go.Scatter(x=[rel[i, 0]], y=[rel[i, 1]], customdata=[times[i]])],
            traces=[3],
            name=str(i),
        )
        for i in range(len(sample))
    ]
    fig.update_layout(
        **base_layout(f"Локальная траектория около {result.point_name}"),
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "x": 0.0,
                "y": -0.12,
                "buttons": [
                    {
                        "label": "Play",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": 35, "redraw": False},
                                "fromcurrent": True,
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                    {
                        "label": "Pause",
                        "method": "animate",
                        "args": [[None], {"frame": {"duration": 0}, "mode": "immediate"}],
                    },
                ],
            }
        ],
    )
    style_xy_axes(fig, "Δx", "Δy")
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    fig.update_xaxes(range=[-radius, radius])
    fig.update_yaxes(range=[-radius, radius])
    return fig


def build_distance(result: SimulationResult, sample: np.ndarray) -> go.Figure:
    """Build the distance-over-time figure."""

    color = DISTANCE_UNSTABLE_COLOR
    if result.point_name not in {"L1", "L2", "L3"}:
        color = DISTANCE_STABLE_COLOR
    max_index = int(np.argmax(result.rel_distance_xy))
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=result.times[sample],
            y=result.rel_distance_xy[sample],
            mode="lines",
            line={"color": color, "width": 3},
            name="r(t)",
            hovertemplate="t=%{x:.3f}<br>r=%{y:.6f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[result.times[max_index]],
            y=[result.rel_distance_xy[max_index]],
            mode="markers",
            marker={"size": 10, "color": "#ffffff", "line": {"color": color, "width": 2}},
            name="max r",
            hovertemplate="max r=%{y:.6f}<br>t=%{x:.3f}<extra></extra>",
        )
    )
    fig.update_layout(**base_layout("Отклонение r(t)"))
    style_xy_axes(fig, "t", "r(t)")
    fig.update_xaxes(range=[0.0, float(result.times[-1])])
    return fig


def build_local_3d(result: SimulationResult, sample: np.ndarray) -> go.Figure:
    """Build the local 3D trajectory figure."""

    rel = result.rel_states[sample]
    times = result.times[sample]
    radius = local_radius(result.rel_states)
    z_radius = max(float(np.max(np.abs(result.rel_states[:, 2]))), radius * 0.5)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter3d(
            x=rel[:, 0],
            y=rel[:, 1],
            z=rel[:, 2],
            customdata=times,
            mode="lines",
            line={"color": LOCAL_3D_COLOR, "width": 5},
            name="3D-траектория",
            hovertemplate=(
                "t=%{customdata:.3f}<br>Δx=%{x:.6f}<br>Δy=%{y:.6f}<br>Δz=%{z:.6f}<extra></extra>"
            ),
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=[0.0],
            y=[0.0],
            z=[0.0],
            mode="markers",
            marker={"size": 7, "color": TARGET_COLOR},
            name=result.point_name,
            hovertemplate=f"{result.point_name}<br>Δx=0<br>Δy=0<br>Δz=0<extra></extra>",
        )
    )
    layout = base_layout("Локальный 3D-вид")
    layout["margin"] = {"l": 10, "r": 10, "t": 52, "b": 10}
    fig.update_layout(
        **layout,
        scene={
            "xaxis": {
                "title": "Δx",
                "backgroundcolor": "#111827",
                "gridcolor": AXIS_COLOR,
                "range": [-radius, radius],
            },
            "yaxis": {
                "title": "Δy",
                "backgroundcolor": "#111827",
                "gridcolor": AXIS_COLOR,
                "range": [-radius, radius],
            },
            "zaxis": {
                "title": "Δz",
                "backgroundcolor": "#111827",
                "gridcolor": AXIS_COLOR,
                "range": [-z_radius, z_radius],
            },
            "camera": {"eye": {"x": 1.5, "y": -1.8, "z": 1.0}},
            "aspectmode": "manual",
            "aspectratio": {"x": 1.0, "y": 1.0, "z": 0.65},
        },
    )
    return fig


def build_global_context(result: SimulationResult, sample: np.ndarray) -> go.Figure:
    """Build a compact global context map."""

    states = result.states[sample]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=states[:, 0],
            y=states[:, 1],
            customdata=result.times[sample],
            mode="lines",
            line={"color": TRAJECTORY_COLOR, "width": 2},
            name="Траектория",
            hovertemplate="t=%{customdata:.3f}<br>x=%{x:.6f}<br>y=%{y:.6f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[-result.system.mu, 1.0 - result.system.mu],
            y=[0.0, 0.0],
            mode="markers+text",
            marker={"size": [16, 11], "color": ["#ffb000", "#4ea1ff"]},
            text=["Солнце", "Земля"],
            textposition="top center",
            name="Тела системы",
            hovertemplate="%{text}<br>x=%{x:.6f}<br>y=%{y:.6f}<extra></extra>",
        )
    )
    for name, coords in result.points.items():
        color = TARGET_COLOR if name == result.point_name else MUTED_COLOR
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
                hovertemplate=f"{name}<br>x=%{{x:.6f}}<br>y=%{{y:.6f}}<extra></extra>",
            ),
        )
    fig.update_layout(**base_layout("Контекст системы"))
    style_xy_axes(fig, "x", "y")
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    fig.update_xaxes(range=[-1.15, 1.15])
    fig.update_yaxes(range=[-0.95, 0.95])
    return fig


def build_comparison(results: list[SimulationResult]) -> go.Figure:
    """Build a distance comparison figure for several simulation runs."""

    fig = go.Figure()
    for result in results:
        color = DISTANCE_UNSTABLE_COLOR
        if result.point_name not in {"L1", "L2", "L3"}:
            color = DISTANCE_STABLE_COLOR
        fig.add_trace(
            go.Scatter(
                x=result.times,
                y=result.rel_distance_xy,
                mode="lines",
                line={"color": color, "width": 3},
                name=f"{result.point_name}: {result.config.mode_name}",
                hovertemplate="t=%{x:.3f}<br>r=%{y:.6f}<extra></extra>",
            )
        )
    fig.update_layout(**base_layout("Сравнение устойчивости", showlegend=True))
    style_xy_axes(fig, "t", "r(t)")
    return fig
