"""Lightweight Material-style line icons drawn at runtime.

These are rendered with :class:`QPainter` onto transparent pixmaps so the UI
does not depend on any external icon theme, font or asset directory. Icons are
simple two-tone line glyphs in the current highlight color, matching Material's
"outlined" look.
"""

from __future__ import annotations

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

_ACCENT = "#3d6bd0"
_SIZE = 24  # px, matches a typical toolbar icon


def _pen(width: float = 2.0) -> QPen:
    pen = QPen(QColor(_ACCENT))
    pen.setWidthF(width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def _canvas() -> tuple[QPixmap, QPainter]:
    pix = QPixmap(_SIZE, _SIZE)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    return pix, painter


def _icon(spec: str) -> QIcon:
    """Build an icon from a small drawing spec.

    Commands: ``L x1 y1 x2 y2`` (line), ``E cx cy rx ry`` (ellipse),
    ``P x1,y1 x2,y2 ...`` (polygon/polyline), ``D x y r`` (dot/filled circle).
    """
    pix, p = _canvas()
    p.setPen(_pen())
    for seg in spec.split(";"):
        parts = seg.split()
        if not parts:
            continue
        cmd, args = parts[0], parts[1:]
        if cmd == "L":
            x1, y1, x2, y2 = map(float, args[:4])
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        elif cmd == "E":
            cx, cy, rx, ry = map(float, args[:4])
            p.drawEllipse(QPointF(cx, cy), rx, ry)
        elif cmd == "P":
            pts = [QPointF(*map(float, a.split(","))) for a in args]
            path = QPainterPath()
            path.moveTo(pts[0])
            for pt in pts[1:]:
                path.lineTo(pt)
            p.drawPath(path)
        elif cmd.startswith("D"):
            cx, cy, r = map(float, args[:3])
            p.setBrush(QColor(_ACCENT))
            p.drawEllipse(QPointF(cx, cy), r, r)
            p.setBrush(Qt.BrushStyle.NoBrush)
    p.end()
    return QIcon(pix)


def make(name: str) -> QIcon:
    """Return the icon for a named tool/action, or an empty icon if unknown."""
    specs = {
        "circle": "E 12 12 4 4",
        "ellipse": "E 12 12 5 3",
        "polygon": "P 12,4 20,9 17,19 7,19 4,9",
        "freehand": "P 3,18 6,8 9,14 12,6 15,13 18,7 21,15",
        "detect": "E 12 12 5 5;E 12 12 9 9;D 12 12 1.5",
        "move": "L 12 3 12 21;L 3 12 21 12;L 6 6 12 12 6 18;L 18 6 12 12 18 18",
        "delete": "P 5,7 19,7 10,20 8,10;D 15 11 1",
        "remove_all": "P 4,8 20,8 12,20;L 3 8 21 8;L 10 4 14 4",
        "unit_line": "L 3 12 21 12;L 7 8 7 16;L 17 8 17 16;D 3 12 1.5;D 21 12 1.5",
        "graph": "L 4 20 20 20;L 7 16 7 8;L 12 16 12 4;L 17 16 17 10",
    }
    spec = specs.get(name)
    if spec is None:
        return QIcon()
    return _icon(spec)
