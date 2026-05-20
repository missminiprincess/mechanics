"""Plotly figures for interactive CR3BP dashboards."""

import numpy as np
import plotly.graph_objects as go  # type: ignore[import-untyped]

from mechanics.core.dynamics import jacobi_constant
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

COORD_UNIT = "норм. ед."
TIME_UNIT = "норм. время"


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
            hovertemplate=(
                f"t=%{{customdata:.3f}} {TIME_UNIT}<br>"
                f"Δx=%{{x:.6f}} {COORD_UNIT}<br>"
                f"Δy=%{{y:.6f}} {COORD_UNIT}<extra></extra>"
            ),
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
            hovertemplate=(
                f"{result.point_name}<br>Δx=0 {COORD_UNIT}<br>Δy=0 {COORD_UNIT}<extra></extra>"
            ),
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
            hovertemplate=(
                f"Δx=%{{x:.6f}} {COORD_UNIT}<br>Δy=%{{y:.6f}} {COORD_UNIT}<extra></extra>"
            ),
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
            hovertemplate=(
                f"t=%{{customdata:.3f}} {TIME_UNIT}<br>"
                f"Δx=%{{x:.6f}} {COORD_UNIT}<br>"
                f"Δy=%{{y:.6f}} {COORD_UNIT}<extra></extra>"
            ),
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
    slider_steps = [
        {
            "method": "animate",
            "label": f"{times[i]:.2f}",
            "args": [
                [str(i)],
                {
                    "mode": "immediate",
                    "frame": {"duration": 0, "redraw": False},
                    "transition": {"duration": 0},
                },
            ],
        }
        for i in range(len(sample))
    ]
    layout = base_layout(f"Локальная траектория около {result.point_name}")
    layout["margin"] = {"l": 54, "r": 24, "t": 52, "b": 96}
    fig.update_layout(
        **layout,
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "x": 0.0,
                "y": -0.2,
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
        sliders=[
            {
                "active": 0,
                "x": 0.18,
                "y": -0.16,
                "len": 0.78,
                "currentvalue": {"prefix": "t = ", "suffix": f" {TIME_UNIT}"},
                "pad": {"t": 0, "b": 0},
                "steps": slider_steps,
            }
        ],
    )
    style_xy_axes(fig, f"Δx, {COORD_UNIT}", f"Δy, {COORD_UNIT}")
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
            hovertemplate=(f"t=%{{x:.3f}} {TIME_UNIT}<br>r=%{{y:.6f}} {COORD_UNIT}<extra></extra>"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[result.times[max_index]],
            y=[result.rel_distance_xy[max_index]],
            mode="markers",
            marker={"size": 10, "color": "#ffffff", "line": {"color": color, "width": 2}},
            name="max r",
            hovertemplate=(
                f"max r=%{{y:.6f}} {COORD_UNIT}<br>t=%{{x:.3f}} {TIME_UNIT}<extra></extra>"
            ),
        )
    )
    fig.add_hline(
        y=result.config.escape_threshold,
        line={"color": "#f8fafc", "width": 1, "dash": "dash"},
        annotation_text=f"порог {result.config.escape_threshold:g} {COORD_UNIT}",
        annotation_position="top left",
    )
    fig.update_layout(**base_layout("Отклонение r(t)"))
    style_xy_axes(fig, f"t, {TIME_UNIT}", f"r(t), {COORD_UNIT}")
    fig.update_xaxes(range=[0.0, float(result.times[-1])])
    return fig


def build_jacobi(result: SimulationResult, sample: np.ndarray) -> go.Figure:
    """Build a Jacobi-constant drift figure."""

    values = jacobi_constant(result.states, result.system.mu)
    delta = values - values[0]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=result.times[sample],
            y=delta[sample],
            mode="lines",
            line={"color": "#facc15", "width": 3},
            name="ΔC(t)",
            hovertemplate=f"t=%{{x:.3f}} {TIME_UNIT}<br>ΔC=%{{y:.3e}}<extra></extra>",
        )
    )
    fig.update_layout(**base_layout("Контроль интеграла Якоби"))
    style_xy_axes(fig, f"t, {TIME_UNIT}", "ΔC(t), безразм.")
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
                f"t=%{{customdata:.3f}} {TIME_UNIT}<br>"
                f"Δx=%{{x:.6f}} {COORD_UNIT}<br>"
                f"Δy=%{{y:.6f}} {COORD_UNIT}<br>"
                f"Δz=%{{z:.6f}} {COORD_UNIT}<extra></extra>"
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
            hovertemplate=(
                f"{result.point_name}<br>Δx=0 {COORD_UNIT}<br>"
                f"Δy=0 {COORD_UNIT}<br>Δz=0 {COORD_UNIT}<extra></extra>"
            ),
        )
    )
    layout = base_layout("Локальный 3D-вид")
    layout["margin"] = {"l": 10, "r": 10, "t": 52, "b": 10}
    fig.update_layout(
        **layout,
        scene={
            "xaxis": {
                "title": f"Δx, {COORD_UNIT}",
                "backgroundcolor": "#111827",
                "gridcolor": AXIS_COLOR,
                "range": [-radius, radius],
            },
            "yaxis": {
                "title": f"Δy, {COORD_UNIT}",
                "backgroundcolor": "#111827",
                "gridcolor": AXIS_COLOR,
                "range": [-radius, radius],
            },
            "zaxis": {
                "title": f"Δz, {COORD_UNIT}",
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
            hovertemplate=(
                f"t=%{{customdata:.3f}} {TIME_UNIT}<br>"
                f"x=%{{x:.6f}} {COORD_UNIT}<br>"
                f"y=%{{y:.6f}} {COORD_UNIT}<extra></extra>"
            ),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[-result.system.mu, 1.0 - result.system.mu],
            y=[0.0, 0.0],
            mode="markers+text",
            marker={"size": [16, 11], "color": ["#ffb000", "#4ea1ff"]},
            text=[result.system.primary_name, result.system.secondary_name],
            textposition="top center",
            name="Тела системы",
            hovertemplate=(
                f"%{{text}}<br>x=%{{x:.6f}} {COORD_UNIT}<br>"
                f"y=%{{y:.6f}} {COORD_UNIT}<extra></extra>"
            ),
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
                hovertemplate=(
                    f"{name}<br>x=%{{x:.6f}} {COORD_UNIT}<br>"
                    f"y=%{{y:.6f}} {COORD_UNIT}<extra></extra>"
                ),
            ),
        )
    fig.update_layout(**base_layout("Контекст системы"))
    style_xy_axes(fig, f"x, {COORD_UNIT}", f"y, {COORD_UNIT}")
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    fig.update_xaxes(range=[-1.15, 1.15])
    fig.update_yaxes(range=[-0.95, 0.95])
    return fig


def build_comparison(results: list[SimulationResult]) -> go.Figure:
    """Build a distance comparison figure for several simulation runs."""

    return build_named_distance_comparison(
        [(f"{result.point_name}: {result.config.mode_name}", result) for result in results],
        "Сравнение устойчивости",
    )


def build_named_distance_comparison(
    named_results: list[tuple[str, SimulationResult]], title: str
) -> go.Figure:
    """Build a distance comparison figure with custom trace names."""

    fig = go.Figure()
    for name, result in named_results:
        color = DISTANCE_UNSTABLE_COLOR
        if result.point_name not in {"L1", "L2", "L3"}:
            color = DISTANCE_STABLE_COLOR
        fig.add_trace(
            go.Scatter(
                x=result.times,
                y=result.rel_distance_xy,
                mode="lines",
                line={"color": color, "width": 3},
                name=name,
                hovertemplate=(
                    f"t=%{{x:.3f}} {TIME_UNIT}<br>r=%{{y:.6f}} {COORD_UNIT}<extra></extra>"
                ),
            )
        )
    fig.update_layout(**base_layout(title, showlegend=True))
    style_xy_axes(fig, f"t, {TIME_UNIT}", f"r(t), {COORD_UNIT}")
    return fig
