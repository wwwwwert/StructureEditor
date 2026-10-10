"""Freehand amorphous selection tool."""

from __future__ import annotations

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QBrush, QColor, QPainterPath, QPolygonF

from structure_editor.tools.selection_tool import SelectionTool, pen_from


class FreehandTool(SelectionTool):
    """Capture a hand-drawn region; its filled area is used directly."""

    def __init__(self, controller) -> None:
        super().__init__(controller)
        self._recording = False
        self._points = []
        self._path_item = None

    def on_press(self, event) -> None:
        self._recording = True
        pt = self.scene_point(event)
        self._points = [pt]
        from PyQt6.QtGui import QPainterPath

        self._path_item = self.scene.addPath(QPainterPath())
        self._path_item.setPen(pen_from(self.config.render_color(), 2, dash=False))
        self._path_item.setBrush(QBrush(QColor(0, 0, 0, 0)))

    def on_move(self, event) -> None:
        if not self._recording:
            return
        self._points.append(self.scene_point(event))
        path = QPainterPath()
        path.addPolygon(QPolygonF([QPointF(*p) for p in self._points]))
        self._path_item.setPath(path)

    def on_release(self, event) -> None:
        if not self._recording:
            return
        self._recording = False
        if len(self._points) < 3:
            self.scene.removeItem(self._path_item)
            self._path_item = None
            return

        area = self._signed_area(self._points)
        tag = self.controller.next_tag("shape")
        self._path_item.setData(1, "amorphous_region")
        self._path_item.setData(0, tag)
        self.submit("amorphous", ("amorphous", tag, None, abs(area), 0.0))
        self._points = []
        self._path_item = None

    def _signed_area(self, pts) -> float:
        n = len(pts)
        return (
            sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
            / 2.0
        )
