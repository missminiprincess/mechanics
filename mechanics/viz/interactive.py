"""Interactive Plotly dashboard exports."""

from html import escape
from pathlib import Path

import plotly.graph_objects as go  # type: ignore[import-untyped]
import plotly.io as pio  # type: ignore[import-untyped]

from mechanics.core.models import SimulationResult
from mechanics.io.summary import simulation_metrics
from mechanics.viz.interactive_figures import (
    build_comparison,
    build_distance,
    build_global_context,
    build_local_2d,
    build_local_3d,
    sample_indices,
)

TEMPLATE_PATH = Path(__file__).with_name("templates") / "dashboard.html"


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


def _button(tab_id: str, label: str, *, active: bool = False) -> str:
    """Render one tab button."""

    selected = "true" if active else "false"
    return (
        f'<button class="tab-button" data-tab="{tab_id}" aria-selected="{selected}">'
        f"{escape(label)}</button>"
    )


def _panel(tab_id: str, content: str, *, active: bool = False) -> str:
    """Render one tab panel."""

    class_name = "tab-panel is-active" if active else "tab-panel"
    return f'<section id="{tab_id}" class="{class_name}">{content}</section>'


def _metrics_html(result: SimulationResult, sample_count: int) -> str:
    """Build the compact metrics panel."""

    metrics = simulation_metrics(result)
    fields = [
        ("Точка", result.point_name),
        ("Режим", metrics["regime_label"]),
        ("max r", f"{metrics['max_rel_distance_xy']:.6f}"),
        ("t max", f"{result.config.t_max:g}"),
        ("dt", f"{result.config.dt:g}"),
        ("samples", f"{sample_count}/{len(result.times)}"),
        ("final r", f"{metrics['final_rel_distance_xy']:.6f}"),
        ("growth", f"{metrics['growth_ratio']:.2f}x"),
        ("t max r", f"{metrics['max_rel_distance_time']:.3f}"),
    ]
    items = "\n".join(
        (
            f'<div class="metric"><span>{escape(label)}</span>'
            f"<strong>{escape(str(value))}</strong></div>"
        )
        for label, value in fields
    )
    return f'<section class="metrics" aria-label="Параметры запуска">{items}</section>'


def _render_page(title: str, subtitle: str, tabs: list[tuple[str, str, str]]) -> str:
    """Render dashboard HTML from tab content."""

    buttons = "\n".join(
        _button(tab_id, label, active=i == 0) for i, (tab_id, label, _) in enumerate(tabs)
    )
    panels = "\n".join(
        _panel(tab_id, content, active=i == 0) for i, (tab_id, _, content) in enumerate(tabs)
    )
    return TEMPLATE_PATH.read_text(encoding="utf-8").format(
        title=escape(title),
        subtitle=subtitle,
        tab_buttons=buttons,
        tab_panels=panels,
    )


def build_dashboard_html(result: SimulationResult) -> str:
    """Build one responsive interactive dashboard HTML document."""

    sample = sample_indices(result)
    title = f"Интерактивная визуализация около {result.point_name}"
    subtitle = (
        f"{escape(result.system.name)} · μ={result.system.mu:.8g} · "
        f"max r={float(result.rel_distance_xy.max()):.6f}"
    )
    local_2d = _figure_fragment(build_local_2d(result, sample))
    distance = _figure_fragment(build_distance(result, sample))
    local_3d = _figure_fragment(build_local_3d(result, sample))
    context = _figure_fragment(build_global_context(result, sample))
    overview = f"""
      <section class="dashboard">
        <article class="panel plot-local">{local_2d}</article>
        {_metrics_html(result, len(sample))}
        <article class="panel plot-distance">{distance}</article>
      </section>
    """
    space = f"""
      <section class="split-grid">
        <article class="panel plot-three">{local_3d}</article>
        <article class="panel plot-context">{context}</article>
      </section>
    """
    tabs = [("overview", "Локально", overview), ("space", "3D и система", space)]
    return _render_page(title, subtitle, tabs)


def save_dashboard(result: SimulationResult, output_path: Path) -> None:
    """Write one interactive dashboard to HTML."""

    output_path.write_text(build_dashboard_html(result), encoding="utf-8")


def save_showcase_comparison(results: list[SimulationResult], output_path: Path) -> None:
    """Write a comparison dashboard for multiple showcase runs."""

    title = "Сравнение сценариев L1 и L4"
    subtitle = "Сравнение r(t) показывает рост отклонения около L1 и ограниченное движение около L4"
    comparison = _figure_fragment(build_comparison(results))
    content = f'<article class="panel plot-comparison">{comparison}</article>'
    output_path.write_text(
        _render_page(title, escape(subtitle), [("comparison", "Сравнение", content)]),
        encoding="utf-8",
    )
