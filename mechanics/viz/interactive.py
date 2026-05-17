"""Interactive Plotly visualizations."""

from html import escape
from pathlib import Path

import numpy as np
import plotly.graph_objects as go  # type: ignore[import-untyped]
import plotly.io as pio  # type: ignore[import-untyped]

from mechanics.core.models import SimulationResult

PLOT_BG = "#070b14"
PAPER_BG = "#05070d"
GRID_COLOR = "#243041"
AXIS_COLOR = "#4b5568"
TEXT_COLOR = "#f6f8ff"
MUTED_COLOR = "#9ca3af"
TRAJECTORY_COLOR = "#38a3ff"
DISTANCE_UNSTABLE_COLOR = "#ff4d6d"
DISTANCE_STABLE_COLOR = "#7cff7a"
LOCAL_3D_COLOR = "#d28cff"
TARGET_COLOR = "#ff5b5b"
START_COLOR = "#23d160"
END_COLOR = "#ff9f1c"


def _sample_indices(result: SimulationResult) -> np.ndarray:
    """Return stable sample indices for interactive outputs."""

    stride = max(1, result.config.sample_stride)
    indices = np.arange(0, len(result.times), stride, dtype=int)
    if indices[-1] != len(result.times) - 1:
        indices = np.append(indices, len(result.times) - 1)
    return indices


def _base_layout(title: str) -> dict[str, object]:
    """Common Plotly layout settings."""

    return {
        "title": {"text": title, "x": 0.02, "xanchor": "left", "font": {"size": 16}},
        "template": "plotly_dark",
        "autosize": True,
        "paper_bgcolor": PAPER_BG,
        "plot_bgcolor": PLOT_BG,
        "font": {"color": TEXT_COLOR, "size": 12},
        "margin": {"l": 54, "r": 24, "t": 52, "b": 48},
        "showlegend": False,
        "legend": {
            "orientation": "h",
            "x": 0.0,
            "y": 1.08,
            "xanchor": "left",
            "yanchor": "bottom",
            "font": {"size": 11},
        },
    }


def _style_xy_axes(fig: go.Figure, x_title: str, y_title: str) -> None:
    """Apply shared 2D axis styling."""

    fig.update_xaxes(
        title_text=x_title,
        gridcolor=GRID_COLOR,
        zerolinecolor=AXIS_COLOR,
        linecolor=AXIS_COLOR,
        automargin=True,
    )
    fig.update_yaxes(
        title_text=y_title,
        gridcolor=GRID_COLOR,
        zerolinecolor=AXIS_COLOR,
        linecolor=AXIS_COLOR,
        automargin=True,
    )


def _local_radius(rel: np.ndarray) -> float:
    """Return a readable symmetric radius around the selected Lagrange point."""

    return max(float(np.max(np.abs(rel[:, 0]))), float(np.max(np.abs(rel[:, 1]))), 0.001) * 1.18


def _build_local_2d(result: SimulationResult, sample: np.ndarray) -> go.Figure:
    """Build the main local 2D trajectory figure."""

    rel = result.rel_states[sample]
    times = result.times[sample]
    radius = _local_radius(result.rel_states)
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
    fig.update_layout(**_base_layout(f"Локальная траектория около {result.point_name}"))
    _style_xy_axes(fig, "Δx", "Δy")
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    fig.update_xaxes(range=[-radius, radius])
    fig.update_yaxes(range=[-radius, radius])
    return fig


def _build_distance(result: SimulationResult, sample: np.ndarray) -> go.Figure:
    """Build the distance-over-time figure."""

    color = DISTANCE_UNSTABLE_COLOR
    if result.point_name not in {"L1", "L2", "L3"}:
        color = DISTANCE_STABLE_COLOR
    distances = result.rel_distance_xy[sample]
    times = result.times[sample]
    max_index = int(np.argmax(result.rel_distance_xy))
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=times,
            y=distances,
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
    fig.update_layout(**_base_layout("Отклонение r(t)"))
    _style_xy_axes(fig, "t", "r(t)")
    fig.update_xaxes(range=[0.0, float(result.times[-1])])
    return fig


def _build_local_3d(result: SimulationResult, sample: np.ndarray) -> go.Figure:
    """Build the local 3D trajectory figure."""

    rel = result.rel_states[sample]
    times = result.times[sample]
    radius = _local_radius(result.rel_states)
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
    layout = _base_layout("Локальный 3D-вид")
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


def _build_global_context(result: SimulationResult, sample: np.ndarray) -> go.Figure:
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
    fig.update_layout(**_base_layout("Контекст системы"))
    _style_xy_axes(fig, "x", "y")
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    fig.update_xaxes(range=[-1.15, 1.15])
    fig.update_yaxes(range=[-0.95, 0.95])
    return fig


def _figure_fragment(fig: go.Figure) -> str:
    """Render one Plotly figure for embedding inside the dashboard grid."""

    return pio.to_html(
        fig,
        include_plotlyjs=False,
        full_html=False,
        default_width="100%",
        default_height="100%",
        config={"responsive": True, "displaylogo": False},
    )


def _metrics_html(result: SimulationResult, sample_count: int) -> str:
    """Build the compact metrics panel."""

    metrics = [
        ("Точка", result.point_name),
        ("Режим", "неустойчивый" if result.point_name in {"L1", "L2", "L3"} else "устойчивый"),
        ("max r", f"{float(result.rel_distance_xy.max()):.6f}"),
        ("t max", f"{result.config.t_max:g}"),
        ("dt", f"{result.config.dt:g}"),
        ("samples", f"{sample_count}/{len(result.times)}"),
    ]
    items = "\n".join(
        f'<div class="metric"><span>{escape(label)}</span><strong>{escape(value)}</strong></div>'
        for label, value in metrics
    )
    return f'<section class="metrics" aria-label="Параметры запуска">{items}</section>'


def build_dashboard(result: SimulationResult) -> str:
    """Build one responsive interactive dashboard HTML document."""

    sample = _sample_indices(result)
    local_2d = _figure_fragment(_build_local_2d(result, sample))
    distance = _figure_fragment(_build_distance(result, sample))
    local_3d = _figure_fragment(_build_local_3d(result, sample))
    global_context = _figure_fragment(_build_global_context(result, sample))
    title = f"Интерактивная визуализация около {result.point_name}"
    subtitle = (
        f"{escape(result.system.name)} · μ={result.system.mu:.8g} · "
        f"max r={float(result.rel_distance_xy.max()):.6f}"
    )
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <script src="https://cdn.plot.ly/plotly-3.5.0.min.js"
          integrity="sha256-fHbNLP+GlIXN+efbQec78UkemUz3NJp7UmfGxC1tNxs="
          crossorigin="anonymous"></script>
  <style>
    :root {{
      color-scheme: dark;
      --bg: {PAPER_BG};
      --panel: #080d17;
      --panel-border: #1f2937;
      --text: {TEXT_COLOR};
      --muted: {MUTED_COLOR};
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; min-height: 100%; background: var(--bg); color: var(--text); }}
    body {{ font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    main {{ width: min(1560px, 100%); margin: 0 auto; padding: 18px; }}
    header {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 16px;
      padding: 4px 2px 16px;
    }}
    h1 {{ margin: 0; font-size: clamp(20px, 2vw, 30px); font-weight: 760; line-height: 1.12; }}
    .subtitle {{ margin: 6px 0 0; color: var(--muted); font-size: 13px; }}
    .dashboard {{
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(360px, 0.9fr);
      grid-template-areas:
        "local metrics"
        "local distance"
        "three context";
      gap: 16px;
      align-items: stretch;
    }}
    .panel, .metrics {{
      background: var(--panel);
      border: 1px solid var(--panel-border);
      min-width: 0;
      overflow: hidden;
    }}
    .plot-local {{ grid-area: local; height: 620px; }}
    .plot-distance {{ grid-area: distance; height: 330px; }}
    .plot-three {{ grid-area: three; height: 500px; }}
    .plot-context {{ grid-area: context; height: 500px; }}
    .metrics {{
      grid-area: metrics;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 1px;
      background: var(--panel-border);
    }}
    .metric {{ background: var(--panel); padding: 14px 16px; min-width: 0; }}
    .metric span {{
      display: block;
      margin-bottom: 6px;
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0;
    }}
    .metric strong {{
      display: block;
      font-size: 17px;
      line-height: 1.15;
      overflow-wrap: anywhere;
    }}
    .panel > div {{ width: 100%; height: 100%; }}
    @media (max-width: 980px) {{
      main {{ padding: 12px; }}
      header {{ display: block; }}
      .dashboard {{
        grid-template-columns: minmax(0, 1fr);
        grid-template-areas:
          "metrics"
          "local"
          "distance"
          "three"
          "context";
      }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .plot-local {{ height: 520px; }}
      .plot-distance {{ height: 360px; }}
      .plot-three, .plot-context {{ height: 460px; }}
    }}
    @media (max-width: 560px) {{
      main {{ padding: 8px; }}
      h1 {{ font-size: 20px; }}
      .subtitle {{ font-size: 12px; }}
      .dashboard {{ gap: 10px; }}
      .metrics {{ grid-template-columns: minmax(0, 1fr); }}
      .metric {{ padding: 11px 12px; }}
      .metric strong {{ font-size: 15px; }}
      .plot-local {{ height: 430px; }}
      .plot-distance {{ height: 320px; }}
      .plot-three, .plot-context {{ height: 390px; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>{escape(title)}</h1>
        <p class="subtitle">{subtitle}</p>
      </div>
    </header>
    <section class="dashboard">
      <article class="panel plot-local">{local_2d}</article>
      {_metrics_html(result, len(sample))}
      <article class="panel plot-distance">{distance}</article>
      <article class="panel plot-three">{local_3d}</article>
      <article class="panel plot-context">{global_context}</article>
    </section>
  </main>
</body>
</html>
"""


def save_dashboard(result: SimulationResult, output_path: Path) -> None:
    """Write one interactive dashboard to HTML."""

    output_path.write_text(build_dashboard(result), encoding="utf-8")
