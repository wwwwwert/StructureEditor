from __future__ import annotations

import math
from typing import Callable, Optional

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QMouseEvent, QPen
from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QMessageBox

from ..core import detection
from ..core.shapes import (Circle, Ellipse, PolygonShape, TAG_ROLE, UnitLine,
                           ellipse_from_axes, perpendicular, points_to_path)
from .dialogs import ChoiceDialog, UnitLengthDialog

DETECT_METHODS = ["DistanceTransform", "Filter2D", "HoughCircles"]
DETECT_METHODS_ALL = ["DistanceTransform", "HoughCircles"]

BOUND_CIRCLE = "Bound with circle"
BOUND_ELLIPSE = "Bound with ellipse"


def scene_pos(view, event: QMouseEvent) -> QPointF:
    return view.mapToScene(event.position().toPoint())


class Tool:
    """Базовый класс инструмента разметки.

    Вместо bind/unbind спагетти каждый инструмент — конечный автомат,
    получающий события мыши от активного холста. Предпросмотр хранит
    как «сырые» элементы сцен (не входящие в store) и удаляет их
    в cleanup().
    """

    name = "tool"
    has_finish = False

    def __init__(self, editor) -> None:
        self.editor = editor
        self._preview: list = []

    # -- предпросмотр -----------------------------------------------------
    def _make_preview(self, builder, z: int = 100) -> list:
        items = []
        for scene in self.editor.scenes.both:
            item = builder(scene)
            item.setZValue(z)
            items.append(item)
        self._preview.extend(items)
        return items

    def _drop_preview(self) -> None:
        for item in self._preview:
            scene = item.scene()
            if scene is not None:
                scene.removeItem(item)
        self._preview.clear()

    def cleanup(self) -> None:
        self._drop_preview()

    # -- события ----------------------------------------------------------
    def on_press(self, view, event: QMouseEvent) -> None:
        pass

    def on_move(self, view, event: QMouseEvent) -> None:
        pass

    def on_release(self, view, event: QMouseEvent) -> None:
        pass


class CircleTool(Tool):
    """Круг: нажать в центре, оттянуть до границы."""

    name = "circle"

    def __init__(self, editor, on_created: Optional[Callable] = None,
                 one_shot: bool = False) -> None:
        super().__init__(editor)
        self.on_created = on_created
        self.one_shot = one_shot
        self._start: Optional[QPointF] = None
        self._items: list[QGraphicsEllipseItem] = []

    def _pen(self) -> QPen:
        return _solid_pen(self.editor.config.colors["circle_outline"],
                          self.editor.config.sizes["line_width"])

    def on_press(self, view, event: QMouseEvent) -> None:
        self._start = scene_pos(view, event)
        rect = QRectF(self._start, self._start)
        self._items = self._make_preview(
            lambda scene: scene.addEllipse(rect, self._pen()))

    def on_move(self, view, event: QMouseEvent) -> None:
        if self._start is None:
            return
        pos = scene_pos(view, event)
        radius = math.dist((self._start.x(), self._start.y()),
                           (pos.x(), pos.y()))
        rect = QRectF(self._start.x() - radius, self._start.y() - radius,
                      2 * radius, 2 * radius)
        for item in self._items:
            item.setRect(rect)

    def on_release(self, view, event: QMouseEvent) -> None:
        if self._start is None:
            return
        pos = scene_pos(view, event)
        start = self._start
        self.cleanup()
        self._start = None

        radius = math.dist((start.x(), start.y()), (pos.x(), pos.y()))
        if radius < 3:
            return
        shape = Circle(start, radius)
        self.editor.add_shape(shape)
        if self.on_created is not None:
            self.on_created(shape)
        if self.one_shot:
            self.editor.activate_default_tool()

    def cleanup(self) -> None:
        super().cleanup()
        self._items = []
        self._start = None


class CircleDetectTool(CircleTool):
    """Круг + автодетекция всех окружностей с радиусом ±15%."""

    name = "circle_detect"

    def __init__(self, editor):
        super().__init__(editor, on_created=self._detect)

    def _detect(self, drawn: Circle) -> None:
        self.editor.remove_shape(drawn)
        method = ChoiceDialog.ask("Detection method", DETECT_METHODS,
                                  self.editor.canvas)
        if method is None:
            return
        try:
            self.editor.detect_circles_like(method, drawn.radius, drawn.center)
        except detection.DetectionUnavailableError as exc:
            QMessageBox.warning(self.editor.canvas, "Detection unavailable",
                                str(exc))


class EllipseTool(Tool):
    """Эллипс по двум осям: первая ось — протяжкой, вторая — протяжкой
    перпендикулярно (длина задаётся второй протяжкой)."""

    name = "ellipse"

    def __init__(self, editor, on_created: Optional[Callable] = None,
                 one_shot: bool = False) -> None:
        super().__init__(editor)
        self.on_created = on_created
        self.one_shot = one_shot
        self._phase = 0  # 0: ждём ось 1, 1: тянем ось 1, 2: ждём ось 2, 3: тянем ось 2
        self._axis1: Optional[tuple[QPointF, QPointF]] = None
        self._axis2_press: Optional[QPointF] = None
        self._axle_items: list[QGraphicsLineItem] = []
        self._ellipse_item: Optional[QGraphicsEllipseItem] = None

    def _axle_pen(self) -> QPen:
        return _solid_pen(self.editor.config.colors["axle_color"],
                          self.editor.config.sizes["line_width"])

    def _start_axle(self, start: QPointF) -> None:
        line = QGraphicsLineItem(start.x(), start.y(), start.x(), start.y())
        line.setPen(self._axle_pen())
        self._axle_items.extend(self._make_preview(lambda scene: line
                                                   if line.scene() is None
                                                   else scene.addLine(
                                                       line.line(),
                                                       self._axle_pen())))

    def _update_axle(self, end: QPointF) -> None:
        for item in self._axle_items:
            line = item.line()
            item.setLine(line.x1(), line.y1(), end.x(), end.y())

    def on_press(self, view, event: QMouseEvent) -> None:
        pos = scene_pos(view, event)
        if self._phase == 0:
            self._start_axle(pos)
            self._phase = 1
        elif self._phase == 2:
            self._axis2_press = pos
            self._start_axle(pos)
            self._phase = 3

    def on_move(self, view, event: QMouseEvent) -> None:
        pos = scene_pos(view, event)
        if self._phase == 1:
            self._update_axle(pos)
        elif self._phase == 3 and self._axis1 and self._axis2_press:
            self._update_axle(pos)
            self._update_ellipse_preview(pos)

    def _update_ellipse_preview(self, pos: QPointF) -> None:
        a1, a2 = self._axis1
        drag = math.dist((self._axis2_press.x(), self._axis2_press.y()),
                         (pos.x(), pos.y()))
        center = QPointF((a1.x() + a2.x()) / 2, (a1.y() + a2.y()) / 2)
        perp = perpendicular(a2 - a1)
        half = QPointF(perp.x() * drag / 2, perp.y() * drag / 2)
        self._axis2 = (center + half, center - half)

        radius_a = math.dist((a1.x(), a1.y()), (a2.x(), a2.y())) / 2
        radius_b = drag / 2
        angle = math.degrees(math.atan2(a2.y() - a1.y(), a2.x() - a1.x()))
        rect = QRectF(-radius_a, -radius_b, 2 * radius_a, 2 * radius_b)

        if self._ellipse_item is None:
            items = self._make_preview(
                lambda scene: scene.addEllipse(rect, self.editor.tools_dashed_pen("oval_color")))
            self._ellipse_item = items[0]
            self._ellipse_item.setPos(center)
            self._ellipse_item.setRotation(angle)
        else:
            self._ellipse_item.setRect(rect)
            self._ellipse_item.setPos(center)
            self._ellipse_item.setRotation(angle)

    def on_release(self, view, event: QMouseEvent) -> None:
        pos = scene_pos(view, event)
        if self._phase == 1:
            start = QPointF(self._axle_items[0].line().p1())
            if math.dist((start.x(), start.y()), (pos.x(), pos.y())) < 3:
                self.cleanup()
                self._phase = 0
                return
            self._axis1 = (start, pos)
            self._phase = 2
        elif self._phase == 3:
            self._finish()

    def _finish(self) -> None:
        if self._axis1 is None or self._axis2 is None:
            self.cleanup()
            self._reset()
            return
        shape = ellipse_from_axes(self._axis1, self._axis2)
        self.cleanup()
        self._reset()
        self.editor.add_shape(shape)
        if self.on_created is not None:
            self.on_created(shape)
        if self.one_shot:
            self.editor.activate_default_tool()

    def _reset(self) -> None:
        self._phase = 0
        self._axis1 = None
        self._axis2 = None
        self._axis2_press = None
        self._axle_items = []
        self._ellipse_item = None

    def cleanup(self) -> None:
        super().cleanup()
        self._reset()


class PolyhedronTool(Tool):
    """Полиэдр: последовательные рёбра от вершины к вершине (протяжкой).
    Близкие к существующей вершине точки прилипают к ней. Замыкание —
    кнопкой Finish (или Enter)."""

    name = "polyhedron"
    has_finish = True

    def __init__(self, editor) -> None:
        super().__init__(editor)
        self.vertices: list[QPointF] = []
        self._edge_items: list = []
        self._outline_items: list = []
        self._start: Optional[QPointF] = None
        self._snap_radius = editor.config.sizes["vertex_circle_radius"]

    def _edge_pen(self):
        from ..core.shapes import dashed_pen
        return dashed_pen(self.editor.config, "edge_color")

    def _snap(self, pos: QPointF) -> QPointF:
        for vertex in self.vertices:
            if math.dist((vertex.x(), vertex.y()),
                         (pos.x(), pos.y())) <= 2 * self._snap_radius:
                return QPointF(vertex)
        return pos

    def _refresh_outline(self) -> None:
        for item in self._outline_items:
            scene = item.scene()
            if scene is not None:
                scene.removeItem(item)
        self._outline_items.clear()
        if len(self.vertices) >= 2:
            from PyQt6.QtGui import QPolygonF
            polygon = QPolygonF(self.vertices)
            self._outline_items = self._make_preview(
                lambda scene: scene.addPolygon(polygon, self._edge_pen()))

    def on_press(self, view, event: QMouseEvent) -> None:
        pos = self._snap(scene_pos(view, event))
        self._start = pos
        if pos not in self.vertices:
            self.vertices.append(pos)
            radius = self._snap_radius
            rect = QRectF(pos.x() - radius, pos.y() - radius,
                          2 * radius, 2 * radius)
            from PyQt6.QtGui import QBrush
            brush = QBrush(QColor(self.editor.config.colors["vertex_fill"]))
            pen = QPen(Qt.PenStyle.NoPen)
            self._make_preview(
                lambda scene: scene.addEllipse(rect, pen, brush))
        start = pos
        self._edge_items.extend(self._make_preview(
            lambda scene: scene.addLine(start.x(), start.y(),
                                        start.x(), start.y(),
                                        self._edge_pen())))

    def on_move(self, view, event: QMouseEvent) -> None:
        if self._start is None:
            return
        pos = self._snap(scene_pos(view, event))
        for item in self._edge_items:
            line = item.line()
            item.setLine(line.x1(), line.y1(), pos.x(), pos.y())

    def on_release(self, view, event: QMouseEvent) -> None:
        if self._start is None:
            return
        pos = self._snap(scene_pos(view, event))
        same_point = math.dist((self._start.x(), self._start.y()),
                               (pos.x(), pos.y())) < 1e-6
        if not same_point and pos not in self.vertices:
            self.vertices.append(pos)
        for item in self._edge_items:
            scene = item.scene()
            if scene is not None:
                scene.removeItem(item)
        self._edge_items.clear()
        self._start = None
        if not same_point:
            self._refresh_outline()

    def finish(self) -> None:
        """Завершить построение: выбрать обрамляющую фигуру."""
        vertices = [QPointF(v) for v in self.vertices]
        self.cleanup()
        if len(vertices) < 3:
            self.editor.activate_default_tool()
            return
        choice = ChoiceDialog.ask(
            "Bounding figure", [BOUND_CIRCLE, BOUND_ELLIPSE],
            self.editor.canvas)
        if choice is None:
            self.editor.activate_default_tool()
            return

        def bound_created(bound_shape):
            self.editor.add_shape(
                PolygonShape(vertices, "polyhedron", bound_shape))

        if choice == BOUND_CIRCLE:
            self.editor.set_tool(CircleTool(self.editor, bound_created,
                                            one_shot=True))
        else:
            self.editor.set_tool(EllipseTool(self.editor, bound_created,
                                             one_shot=True))

    def cleanup(self) -> None:
        super().cleanup()
        self.vertices.clear()
        self._edge_items = []
        self._outline_items = []
        self._start = None


class FreehandTool(Tool):
    """Аморфная область: обвести границу вручную."""

    name = "freehand"

    def __init__(self, editor) -> None:
        super().__init__(editor)
        self._points: list[QPointF] = []

    def on_press(self, view, event: QMouseEvent) -> None:
        self._points = [scene_pos(view, event)]
        path = points_to_path(self._points)
        self._make_preview(lambda scene: scene.addPath(path))

    def on_move(self, view, event: QMouseEvent) -> None:
        if not self._points:
            return
        self._points.append(scene_pos(view, event))
        path = points_to_path(self._points)
        for item in self._preview:
            item.setPath(path)

    def on_release(self, view, event: QMouseEvent) -> None:
        if not self._points:
            return
        points = self._points[::5]  # как в оригинале: каждая 5-я точка
        self.cleanup()
        if len(points) < 3:
            return
        choice = ChoiceDialog.ask(
            "Bounding figure",
            ["Use area of hand-drawn figure", BOUND_CIRCLE, BOUND_ELLIPSE],
            self.editor.canvas)
        if choice is None:
            return
        if choice == "Use area of hand-drawn figure":
            self.editor.add_shape(PolygonShape(points, "amorphous"))
            return

        polygon = PolygonShape(points, "amorphous")
        self.editor.add_shape(polygon)

        def bound_created(bound_shape):
            self.editor.bind_shape(polygon, bound_shape)

        if choice == BOUND_CIRCLE:
            self.editor.set_tool(CircleTool(self.editor, bound_created,
                                            one_shot=True))
        else:
            self.editor.set_tool(EllipseTool(self.editor, bound_created,
                                             one_shot=True))

    def cleanup(self) -> None:
        super().cleanup()
        self._points = []


class UnitLineTool(Tool):
    """Единичный отрезок: протянуть линию, ввести её реальную длину."""

    name = "unit_line"

    def __init__(self, editor) -> None:
        super().__init__(editor)
        self._start: Optional[QPointF] = None
        self._items: list = []

    def _pen(self) -> QPen:
        return _solid_pen(self.editor.config.colors["unit_line_color"],
                          self.editor.config.sizes["unit_line_width"])

    def on_press(self, view, event: QMouseEvent) -> None:
        self._start = scene_pos(view, event)
        start = self._start
        self._items = self._make_preview(
            lambda scene: scene.addLine(start.x(), start.y(),
                                        start.x(), start.y(), self._pen()))

    def on_move(self, view, event: QMouseEvent) -> None:
        if self._start is None:
            return
        pos = scene_pos(view, event)
        for item in self._items:
            item.setLine(self._start.x(), self._start.y(),
                         pos.x(), pos.y())

    def on_release(self, view, event: QMouseEvent) -> None:
        if self._start is None:
            return
        end = scene_pos(view, event)
        start = self._start
        self.cleanup()
        length_px = math.dist((start.x(), start.y()),
                              (end.x(), end.y()))
        if length_px < 3:
            return
        result = UnitLengthDialog.ask(self.editor.canvas)
        if result is None:
            return
        length, unit_type = result
        self.editor.set_unit(length, length_px, unit_type)
        self.editor.replace_unit_line(UnitLine(start, end))
        self.editor.activate_default_tool()

    def cleanup(self) -> None:
        super().cleanup()
        self._items = []
        self._start = None


class MoveTool(Tool):
    """Перемещение фигур перетаскиванием."""

    name = "move"

    def __init__(self, editor) -> None:
        super().__init__(editor)
        self._shape = None
        self._last: Optional[QPointF] = None

    def on_press(self, view, event: QMouseEvent) -> None:
        item = view.itemAt(event.position().toPoint())
        if item is None:
            return
        shape = self.editor.store.by_tag(item.data(TAG_ROLE))
        if shape is not None:
            self._shape = shape
            self._last = scene_pos(view, event)

    def on_move(self, view, event: QMouseEvent) -> None:
        if self._shape is None or self._last is None:
            return
        pos = scene_pos(view, event)
        self._shape.move_by(pos.x() - self._last.x(),
                            pos.y() - self._last.y())
        self._last = pos

    def on_release(self, view, event: QMouseEvent) -> None:
        if self._shape is not None:
            self.editor.shapes_changed.emit()
        self._shape = None
        self._last = None


class RemoveTool(Tool):
    """Удаление фигур кликом."""

    name = "remove"

    def on_press(self, view, event: QMouseEvent) -> None:
        item = view.itemAt(event.position().toPoint())
        if item is None:
            return
        tag = item.data(TAG_ROLE)
        shape = self.editor.store.by_tag(tag)
        if shape is None:
            return
        if isinstance(shape, UnitLine):
            QMessageBox.warning(
                self.editor.canvas, "Unit line",
                'To create new unit line use "Select unit line" function')
            return
        self.editor.remove_shape(shape)


class PointerTool(Tool):
    """Инструмент по умолчанию — ничего не делает."""

    name = "pointer"


def _solid_pen(color: str, width: float) -> QPen:
    pen = QPen(QColor(color), width)
    pen.setCosmetic(True)
    return pen
