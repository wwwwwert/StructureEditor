"""HTML/CSV export of the measurement table (replaces dataframe-image)."""

from __future__ import annotations

import pandas as pd

from structure_editor.model.objects_manager import ObjectsManager


def to_dataframe(manager: ObjectsManager, unit_type: str) -> pd.DataFrame:
    """Turn measurement rows into a labelled dataframe for export/display."""
    rows = manager.lines
    df = pd.DataFrame(
        rows,
        columns=["Structure Type", "Bounding Figure", "Dimension", "Area"],
    )
    df["Area"] = df["Area"].astype(float)
    # Rename header to carry the physical unit.
    df.rename(columns={"Area": f"Area ({unit_type}^2)"}, inplace=True)
    return df


def to_html(manager: ObjectsManager, unit_type: str) -> str:
    """Return a standalone HTML string with the measurement table."""
    df = to_dataframe(manager, unit_type)
    return df.to_html(index=False, border=0)


def to_csv_path(manager: ObjectsManager, unit_type: str, path: str) -> None:
    """Write the measurement table to a CSV file at *path*."""
    df = to_dataframe(manager, unit_type)
    df.to_csv(path, index=False)
