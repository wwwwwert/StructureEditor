"""Theme helpers: load the packaged QSS stylesheet."""

from __future__ import annotations

from pathlib import Path

_STYLE_PATH = Path(__file__).resolve().parent / "style.qss"


def load_theme() -> str:
    """Return the contents of the QSS stylesheet as a string."""
    return _STYLE_PATH.read_text(encoding="utf-8")
