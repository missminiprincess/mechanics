"""Interactive Plotly dashboard exports."""

from html import escape
from pathlib import Path
from typing import cast

import plotly.graph_objects as go  # type: ignore[import-untyped]
import plotly.io as pio  # type: ignore[import-untyped]

from mechanics.core.models import SimulationResult
from mechanics.io.summary import simulation_metrics
from mechanics.viz.interactive_figures import (
    build_comparison,
    build_distance,
    build_global_context,
    build_jacobi,
    build_local_2d,
    build_local_3d,
    build_named_distance_comparison,
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
    max_distance_km = cast(float, metrics["max_rel_distance_km"])
    fields = [
        ("Точка", result.point_name),
        ("Режим", metrics["regime_label"]),
        ("max r", f"{metrics['max_rel_distance_xy']:.6f}"),
        ("max r, км", f"{max_distance_km / 1_000_000:.2f} млн"),
        ("t max", f"{result.config.t_max:g}"),
        ("t unit", f"{result.system.time_unit_s / 86_400.0:.1f} дней"),
        ("dt", f"{result.config.dt:g}"),
        ("samples", f"{sample_count}/{len(result.times)}"),
        ("final r", f"{metrics['final_rel_distance_xy']:.6f}"),
        ("growth", f"{metrics['growth_ratio']:.2f}x"),
        ("t max r", f"{metrics['max_rel_distance_time']:.3f}"),
        ("escape", "нет" if metrics["escape_time"] is None else f"{metrics['escape_time']:.3f}"),
        ("ΔC max", f"{metrics['jacobi_delta_max_abs']:.2e}"),
        ("линеар.", metrics["linear_stability"]),
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


def _run_dashboard_content(result: SimulationResult) -> str:
    """Render all dashboard sections for one simulation result."""

    sample = sample_indices(result)
    local_2d = _figure_fragment(build_local_2d(result, sample))
    distance = _figure_fragment(build_distance(result, sample))
    local_3d = _figure_fragment(build_local_3d(result, sample))
    context = _figure_fragment(build_global_context(result, sample))
    jacobi = _figure_fragment(build_jacobi(result, sample))
    return f"""
      <section class="dashboard">
        <article class="panel plot-local">{local_2d}</article>
        {_metrics_html(result, len(sample))}
        <article class="panel plot-distance">{distance}</article>
      </section>
      <section class="split-grid">
        <article class="panel plot-three">{local_3d}</article>
        <article class="panel plot-context">{context}</article>
      </section>
      <article class="panel plot-jacobi">{jacobi}</article>
    """


def build_dashboard_html(result: SimulationResult) -> str:
    """Build one responsive interactive dashboard HTML document."""

    title = f"Интерактивная визуализация около {result.point_name}"
    subtitle = (
        f"{escape(result.system.name)} · μ={result.system.mu:.8g} · "
        f"max r={float(result.rel_distance_xy.max()):.6f}"
    )
    tabs = [("run", "Запуск", _run_dashboard_content(result))]
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


def _comparison_content(named_results: list[tuple[str, SimulationResult]], title: str) -> str:
    """Render one comparison figure panel."""

    figure = _figure_fragment(build_named_distance_comparison(named_results, title))
    return f'<article class="panel plot-comparison">{figure}</article>'


def save_showcase_dashboard(
    results: list[SimulationResult],
    output_path: Path,
    fair_results: list[tuple[str, SimulationResult]] | None = None,
    amplitude_results: list[tuple[str, SimulationResult]] | None = None,
    dt_results: list[tuple[str, SimulationResult]] | None = None,
) -> None:
    """Write one combined dashboard for the showcase runs."""

    system = results[0].system
    title = f"Система {system.primary_name}-{system.secondary_name}: сценарии L1 и L4"
    subtitle = "Единая интерактивная панель для устойчивого и неустойчивого случаев"
    comparison = _figure_fragment(build_comparison(results))
    tabs = [
        ("l1", "L1", _run_dashboard_content(results[0])),
        ("l4", "L4", _run_dashboard_content(results[1])),
        (
            "comparison",
            "Сравнение",
            f'<article class="panel plot-comparison">{comparison}</article>',
        ),
    ]
    if fair_results is not None:
        tabs.append(
            (
                "fair",
                "Одинаковое возмущение",
                _comparison_content(fair_results, "Одинаковое начальное возмущение"),
            )
        )
    if amplitude_results is not None:
        tabs.append(
            (
                "amplitude",
                "Амплитуды",
                _comparison_content(amplitude_results, "Чувствительность к амплитуде dx"),
            )
        )
    if dt_results is not None:
        tabs.append(
            ("dt", "Шаг dt", _comparison_content(dt_results, "Сравнение численного шага dt"))
        )
    output_path.write_text(_render_page(title, escape(subtitle), tabs), encoding="utf-8")
