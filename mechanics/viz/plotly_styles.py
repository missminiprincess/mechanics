"""Shared Plotly styling constants and helpers."""

import plotly.graph_objects as go  # type: ignore[import-untyped]

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


def base_layout(title: str, *, showlegend: bool = False) -> dict[str, object]:
    """Return common Plotly layout settings."""

    return {
        "title": {"text": title, "x": 0.02, "xanchor": "left", "font": {"size": 16}},
        "template": "plotly_dark",
        "autosize": True,
        "paper_bgcolor": PAPER_BG,
        "plot_bgcolor": PLOT_BG,
        "font": {"color": TEXT_COLOR, "size": 12},
        "margin": {"l": 54, "r": 24, "t": 52, "b": 48},
        "showlegend": showlegend,
        "legend": {
            "orientation": "h",
            "x": 0.0,
            "y": 1.08,
            "xanchor": "left",
            "yanchor": "bottom",
            "font": {"size": 11},
        },
    }


def style_xy_axes(fig: go.Figure, x_title: str, y_title: str) -> None:
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
