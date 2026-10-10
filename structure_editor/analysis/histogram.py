"""Histogram generation with Plotly (replaces matplotlib/seaborn)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px

from structure_editor.model.objects_manager import ObjectsManager

# Accessible categorical palette, ordered so the first structure types get the
# most distinctive hues (consistent across every histogram).
_CATEGORICAL_COLORS = [
    "#4C78A8",  # blue
    "#F58518",  # orange
    "#54A24B",  # green
    "#B45A93",  # magenta
    "#B8B435",  # olive
    "#A55A8B",  # purple
]


def build_figure(manager: ObjectsManager, unit_type: str, pixel_proportion: float):
    """Return a Plotly figure with the size histogram of the *manager* data.

    Sizes are expressed in squared physical units (e.g. micrometre^2).
    """
    rows = manager.lines
    if not rows:
        raise ValueError("No measurements available to plot.")
    df = pd.DataFrame(rows, columns=["structure type", "bound figure type", "dimension", "size"])
    df["size"] = df["size"].astype(float)

    unit_sq = unit_type or "$unit^2$"
    fig = px.histogram(
        df,
        x="size",
        color="structure type",
        nbins=30,
        title="Structure size distribution",
        labels={"size": f"Size ({unit_sq})", "structure type": "Structure type"},
        color_discrete_sequence=_CATEGORICAL_COLORS,
    )
    fig.update_layout(
        template="plotly_white",
        bargap=0.05,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=20, t=70, b=60),
    )
    return fig


def export_figure(fig, path: str) -> None:
    """Render a Plotly *fig* to an image file via kaleido."""
    if not path:
        return
    fig.write_image(path)
