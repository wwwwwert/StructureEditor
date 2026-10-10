"""Configuration loading and DPI-aware scaling for the structure editor."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

# Base reference resolution used to scale sizes to the actual screen.
_REFERENCE_WIDTH = 1280
_REFERENCE_HEIGHT = 800


def _load_config(path: Path) -> dict[str, Any]:
    """Read JSON configuration from *path* and return it as a dictionary."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _scale_value(value: int | float, proportion: float) -> int | float:
    """Scale a numeric *value* by *proportion*, never returning zero."""
    scaled = int(value * proportion)
    return scaled if scaled > 0 else 1


def _scale_spec(
    name: str, value: int | float | dict[str, Any], proportion: float
) -> dict[str, Any]:
    """Recursively scale a single "sizes" entry, preserving structure."""
    if isinstance(value, (int, float)):
        return {name: _scale_value(value, proportion)}
    return {name: {k: _scale_spec(k, v, proportion)[k] for k, v in value.items()}}


class Config:
    """Typed access to the UI configuration, scaled to the current screen.

    Colors and other non-numeric settings are exposed as-is, while numeric
    "sizes" entries are multiplied by a proportion derived from the screen
    resolution relative to a reference base.
    """

    def __init__(self, path: Path, screen_width: int, screen_height: int) -> None:
        self.path = path
        raw = _load_config(path)

        width = screen_width or _REFERENCE_WIDTH
        height = screen_height or _REFERENCE_HEIGHT
        self.screen_proportion = math.sqrt(
            (width * height) / (_REFERENCE_WIDTH * _REFERENCE_HEIGHT)
        )

        sizes = raw.pop("sizes", {})
        scaled_sizes: dict[str, Any] = {}
        for name, value in sizes.items():
            scaled_sizes.update(_scale_spec(name, value, self.screen_proportion))

        self.colors: dict[str, str] = raw  # remaining keys are color names
        self.sizes: dict[str, Any] = scaled_sizes

    def render_color(self) -> str:
        """Return the markup base color (e.g. circle outline)."""
        return self.colors.get("circle_outline", "#4fc3f7")

    def unit_line_color(self) -> str:
        """Return the color used for the unit line."""
        return self.colors.get("unit_line_color", "#69f0ae")

    def unit_line_width(self) -> int:
        """Return the pixel width used for the unit line."""
        sizes = self.sizes
        unit = sizes.get("unit_line_width")
        if isinstance(unit, dict):
            return int(next(iter(unit.values())))
        return int(unit) if unit else 4

    def line_width(self) -> int:
        """Return the pixel width used for ordinary markup lines."""
        sizes = self.sizes
        width = sizes.get("line_width")
        if isinstance(width, dict):
            return int(next(iter(width.values())))
        return int(width) if width else 2


def default_config_path() -> Path:
    """Return the path to the packaged ``config.json``."""
    candidate = Path(__file__).resolve().parent.parent / "config.json"
    if candidate.exists():
        return candidate
    return Path(__file__).resolve().parent / "config.json"


def dependency_hint() -> str:
    """Return a short hint about optional packages installed."""
    return ""
