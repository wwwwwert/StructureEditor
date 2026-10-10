"""Polygon (polyhedron) selection tool."""

from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QBrush, QColor, QCursor, QPainterPath, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsPolygonItem,
)

from structure_editor.tools.selection_tool import SelectionTool, pen_from


class PolygonTool(SelectionTool):
    """Define a polyhedron by clicking successive vertices; closing the shape
    submits it measured directly from its own area.

    (Bounding-figure measurement is left for a future enhancement; the area
    fallback keeps the tool fully usable.)
    """

    VERTEX_HIT = 10.0  # px within which a click snaps to an existing vertex

    def __init__(self, controller) -> None:
        super().__init__(controller)
        self.points: list = []
        self._vertex_items = []
        self._edge_item = None
        self._finished = False

    def cursor(self):
        return QCursor(Qt.CursorShape.PointingHandCursor)

    def on_press(self, event) -> None:
        if self._finished:
            return
        x, y = self.scene_point(event)
        if len(self.points) >= 3 and self._close_to(x, y, self.points[0]):
            self._finish()
            return
        self.points.append([x, y])
        self._draw_vertex(x, y)
        self._redraw_edges()

    def on_move(self, event) -> None:
        if self._finished or not self.points:
            return
        x, y = self.scene_point(event)
        self._redraw_edges((x, y))

    def on_release(self, event) -> None:
        pass

    def _close_to(self, x, y, pt) -> bool:
        return math.hypot(x - pt[0], y - pt[1]) <= self.VERTEX_HIT

    def _draw_vertex(self, x, y) -> None:
        r = self.config.sizes.get("vertex_circle_radius", 5)
        r = r if isinstance(r, int) else 5
        pen = QPen(QColor(self.config.colors.get("vertex_fill", "#ef5350")))
        pen.setWidthF(1)
        pen.setCosmetic(True)
        brush = QBrush(QColor(self.config.colors.get("vertex_fill", "#ef5350")))
        item = QGraphicsEllipseItem(x - r, y - r, 2 * r, 2 * r)
        item.setPen(pen)
        item.setBrush(brush)
        item.setZValue(1)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.scene.addItem(item)
        self._vertex_items.append(item)

    def _redraw_edges(self, hover=None) -> None:
        if self._edge_item is not None:
            self.scene.removeItem(self._edge_item)
            self._edge_item = None
        if not self.points:
            return
        pts = [QPointF(p[0], p[1]) for p in self.points]
        if hover is not None:
            pts.append(QPointF(hover[0], hover[1]))
        path = QPainterPath()
        path.addPolygon(QPolygonF(pts))
        pen = pen_from(self.config.colors.get("edge_color", "#66bb6a"), self.config.line_width())
        item = QGraphicsPathItem(path)
        item.setPen(pen)
        item.setZValue(0)
        self.scene.addItem(item)
        self._edge_item = item

    def _finish(self) -> None:
        if len(self.points) < 3:
            return
        self._finished = True
        for it in self._vertex_items:
            self.scene.removeItem(it)
        self._vertex_items = []
        if self._edge_item is not None:
            self.scene.removeItem(self._edge_item)
            self._edge_item = None

        pts = [QPointF(p[0], p[1]) for p in self.points]
        polygon = QGraphicsPolygonItem(QPolygonF(pts))
        pen = pen_from(
            self.config.colors.get("polygon_outline", "#ffca28"), self.config.line_width()
        )
        polygon.setPen(pen)
        polygon.setZValue(0)
        tag = self.controller.next_tag("shape")
        polygon.setData(0, tag)
        polygon.setData(1, "polygon")
        self.scene.addItem(polygon)

        area = self._polygon_area()
        # Keep the tool active for further polyhedra; cleanup happens elsewhere.
        self.submit("polyhedron", ("polyhedron", tag, None, area, 0.0))
        self._reset()

    def _polygon_area(self) -> float:
        pts = [self.points[i] for i in range(len(self.points))]
        return abs(
            sum(
                pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                for i in range(len(pts))
            )
            / 2.0
        )

    def _reset(self) -> None:
        self.points = []
        self._finished = False

    def end(self) -> None:
        super().end()
        if self._edge_item is not None:
            self.scene.removeItem(self._edge_item)
            self._edge_item = None
        for it in self._vertex_items:
            self.scene.removeItem(it)
        self._vertex_items = []
        self._reset()
