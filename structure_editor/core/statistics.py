from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .shapes import UnitLine

COLUMNS = ["structure type", "bound figure type", "radius", "size"]


def measurements_dataframe(shapes, pixel_proportion: float) -> pd.DataFrame:
    """Таблица измерений по всем фигурам, отсортированная по площади."""
    rows = []
    for shape in shapes:
        if isinstance(shape, UnitLine):
            continue
        rows.append(shape.size_row(pixel_proportion))
    df = pd.DataFrame(rows, columns=COLUMNS)
    return df.sort_values("size").reset_index(drop=True)


def build_histogram(df: pd.DataFrame, unit_type: str) -> go.Figure:
    """Интерактивная гистограмма распределения площадей (в %)."""
    fig = px.histogram(
        df,
        x="size",
        color="structure type",
        barmode="group",
        histnorm="percent",
        labels={"size": f"Sizes of structures ({unit_type}$^2$)",
                "structure type": "Structure Type"},
    )
    fig.update_layout(
        template="plotly_white",
        bargap=0.1,
        legend_title_text="Structure Type",
    )
    return fig


def figure_to_png(fig: go.Figure, scale: int = 2) -> bytes:
    """Отрисовать график в PNG (через kaleido)."""
    return fig.to_image(format="png", scale=scale)


def export_histogram_png(fig: go.Figure, path: str) -> None:
    fig.write_image(path, scale=2)


def export_histogram_html(fig: go.Figure, path: str) -> None:
    fig.write_html(path, include_plotlyjs="cdn")
