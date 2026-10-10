"""Vector Material icons rendered at runtime for a crisp, modern toolbar.

Icons are the official Material Symbols path data (Apache 2.0) embedded as SVG
and painted through :class:`QSvgRenderer` onto a target-sized pixmap. Because
they are vectors they stay sharp on any display scale, and the fill color is
re-applied by the theme so each icon matches the active accent.
"""

from __future__ import annotations

from PyQt6.QtCore import QByteArray, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

# Size of the logical icon canvas in device-independent pixels.
_BASE = 24

# Material Symbols path data (fill-rule paths, currentColor).
_PATHS: dict[str, str] = {
    # image / open
    "image": (
        "M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 "
        "2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"
    ),
    # export / download
    "download": ("M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"),
    # ruler / straighten (unit line calibration)
    "straighten": (
        "M21 6H3c-1.1 0-2 .9-2 2v8c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V8c0-1.1-.9-"
        "2-2-2zm0 10H3V8h2v4h2V8h2v4h2V8h2v4h2V8h2v4h2V8h2v8z"
    ),
    # circle
    "circle": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z",
    # ellipse: a clearly wide, low oval (distinct from the filled circle)
    "ellipse": "M12 4C7.03 4 3 7.58 3 12s4.03 8 9 8 9-3.58 9-8-4.03-8-9-8zm0 3c1.93 0 3.5 1.57 3.5 5s-1.57 5-3.5 5-3.5-1.57-3.5-5 1.57-5 3.5-5z",
    # polygon / hexagon
    "hexagon": (
        "M14 3h-4L4 7v10l6 4h4l6-4V7l-6-4zm1.3 2.8l3.7 2.4v5.6l-3.7 2.4h-2.6"
        "l-3.7-2.4V8.2l3.7-2.4h2.6z"
    ),
    # freehand / draw
    "draw": (
        "M18.85 10.39l1.06-1.06c.78-.78.78-2.05 0-2.83L18.5 5.15a1.98 1.98 0 0 0"
        "-2.83 0l-1.06 1.06 4.24 4.18zm-5.66 5.66l-4.24-4.18 3.54-3.54 4.24 4.18"
        "-3.54 3.54zM3 21l3.54-6.36 5.66 5.66L3 21z"
    ),
    # auto detect / search (material "search")
    "radar": (
        "M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3 "
        "S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99"
        "L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 "
        "11.99 14 9.5 14z"
    ),
    # finger / move-select
    "pan_tool": (
        "M23 5.5V20c0 2.2-1.8 4-4 4h-7.3c-1.08 0-2.1-.43-2.85-1.19L1 14.83s1.26"
        "-1.23 1.3-1.25c.22-.19.49-.29.79-.29.22 0 .42.06.6.16.04.01 4.31 2.46 4.31"
        " 2.46V4c0-1.1.9-2 2-2s2 .9 2 2v7h2V1.5c0-1.1.9-2 2-2s2 .9 2 2V11h2V2.5c0"
        "-1.1.9-2 2-2s2 .9 2 2V11h2V5.5c0-1.1.9-2 2-2s2 .9 2 2z"
    ),
    # delete selected
    "close": "M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z",
    # remove all / delete
    "delete": ("M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"),
    # graph / bar chart
    "bar_chart": "M5 9.2h3V19H5V9.2zM10.6 5h2.8v14h-2.8V5zm5.6 8H19v6h-2.8v-6z",
    # overlay / layers
    "layers": (
        "M11.99 18.54l-7.37-5.73L3 14.07l9 7 9-7-1.63-1.27-7.38 5.74zM12 16l7.36"
        "-5.73L21 9l-9-7-9 7 1.63 1.27L12 16z"
    ),
}


def _material_icon(svg_path: str, color: QColor, size: int) -> QIcon | None:
    """Render one Material path into a themed, DPI-aware icon."""
    color_hex = color.name()
    body = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'width="{size}" height="{size}">'
        f'<path fill="{color_hex}" d="{svg_path}"/></svg>'
    )
    renderer = QSvgRenderer(QByteArray(str.encode(body)))
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    icon = QIcon(pix)
    icon.addPixmap(pix, QIcon.Mode.Normal, QIcon.State.Off)
    return icon


def make(name: str, color: QColor | None = None) -> QIcon:
    """Return the themed Material icon for *name*.

    Falls back to an overlaid material glyph when the exact symbol is not in the
    table, and to a neutral fallback if nothing is known.
    """
    path = _PATHS.get(name)
    if path is None:
        # fall back to a generic rounded square so actions stay visible
        path = _PATHS["layers"]
    color = color or QColor("#e1e6ef")
    size = _BASE
    return _material_icon(path, color, size)


def on_surface() -> QColor:
    """Default icon color for the dark surface."""
    return QColor("#e6e8ef")
