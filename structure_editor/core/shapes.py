from __future__ import annotations

import math
import uuid
from typing import Optional

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QBrush, QColor, QPainterPath, QPen, QPolygonF
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsScene

TAG_ROLE = 0


def dashed_pen(config, color_key: str, width_key: str = "line_width") -> QPen:
    pen = QPen(QColor(config.colors[color_key]), config.sizes[width_key])
    pen.setDashPattern(config.dash_pattern())
    pen.setCosmetic(True)
    return pen


class Shape:
    """Базовый класс фигуры разметки.

    Одна фигура владеет зеркальными элементами сразу в двух сценах:
    сцене выделения (изображение + разметка) и сцене разметки (только
    разметка). Вся манипуляция (перемещение, удаление) выполняется
    один раз и применяется к обеим сценам.

    Координаты фигуры — в системе отображаемого (масштабированного)
    изображения. Пересчёт в реальные единицы выполняется в size_row()
    через pixel_proportion (реальная длина единичного отрезка / пиксели).
    """

    KIND = "shape"
    OUTLINE_KEY = "circle_outline"

    def __init__(self) -> None:
        self.tag: str = f"shape-{uuid.uuid4().hex[:8]}"
        self.items: list[QGraphicsItem] = []

    # -- управление элементами на сценах --------------------------------
    def add_to(self, scenes, config) -> None:
        """Создать зеркальные элементы в обеих сценах."""
        self._create_items(scenes, config)

    def _create_items(self, scenes, config) -> None:  # pragma: no cover
        raise NotImplementedError

    def _register(self, *items: QGraphicsItem) -> None:
        for item in items:
            item.setData(TAG_ROLE, self.tag)
            item.setZValue(10)
            self.items.append(item)

    def _add_to_both(self, scenes, builder) -> None:
        """builder(scene) -> QGraphicsItem; результат регистрируется."""
        for scene in scenes.both:
            self._register(builder(scene))

    def move_by(self, dx: float, dy: float) -> None:
        for item in self.items:
            item.moveBy(dx, dy)

    def destroy(self) -> None:
        for item in self.items:
            scene: Optional[QGraphicsScene] = item.scene()
            if scene is not None:
                scene.removeItem(item)
        self.items.clear()

    def pen(self, config, color_key: Optional[str] = None) -> QPen:
        return dashed_pen(config, color_key or self.OUTLINE_KEY)

    # -- измерения -------------------------------------------------------
    def size_row(self, pixel_proportion: float) -> tuple:
        """Строка таблицы: (тип, тип обрамляющей фигуры, размеры, площадь)."""
        raise NotImplementedError

    def move_center_to(self, center: QPointF) -> None:
        raise NotImplementedError


class Circle(Shape):
    KIND = "circle"
    OUTLINE_KEY = "circle_outline"

    def __init__(self, center: QPointF, radius: float,
                 outline_key: Optional[str] = None) -> None:
        super().__init__()
        self.center = QPointF(center)
        self.radius = float(radius)
        if outline_key:
            self.OUTLINE_KEY = outline_key

    def _create_items(self, scenes, config) -> None:
        pen = self.pen(config)
        rect = QRectF(self.center.x() - self.radius,
                      self.center.y() - self.radius,
                      2 * self.radius, 2 * self.radius)

        def builder(scene):
            return scene.addEllipse(rect, pen)

        self._add_to_both(scenes, builder)

    def move_center_to(self, center: QPointF) -> None:
        delta = center - self.center
        self.center = QPointF(center)
        self.move_by(delta.x(), delta.y())

    def size_row(self, pixel_proportion: float) -> tuple:
        radius = self.radius * pixel_proportion
        return (self.KIND, None, f"{radius:.3f}",
                round(math.pi * radius ** 2, 3))


class Ellipse(Shape):
    KIND = "ellipse"
    OUTLINE_KEY = "oval_color"

    def __init__(self, center: QPointF, radius_a: float, radius_b: float,
                 angle_deg: float) -> None:
        super().__init__()
        self.center = QPointF(center)
        self.radius_a = float(radius_a)
        self.radius_b = float(radius_b)
        self.angle_deg = float(angle_deg)

    def _create_items(self, scenes, config) -> None:
        pen = self.pen(config)
        rect = QRectF(-self.radius_a, -self.radius_b,
                      2 * self.radius_a, 2 * self.radius_b)

        def builder(scene):
            item = scene.addEllipse(rect, pen)
            item.setPos(self.center)
            item.setRotation(self.angle_deg)
            return item

        self._add_to_both(scenes, builder)

    def move_center_to(self, center: QPointF) -> None:
        delta = center - self.center
        self.center = QPointF(center)
        self.move_by(delta.x(), delta.y())

    def size_row(self, pixel_proportion: float) -> tuple:
        a = self.radius_a * pixel_proportion
        b = self.radius_b * pixel_proportion
        return (self.KIND, None, f"{a:.3f}\t{b:.3f}",
                round(math.pi * a * b, 3))


class PolygonShape(Shape):
    """Многоугольник (полиэдр или аморфная область) с опциональной
    обрамляющей фигурой (окружностью или эллипсом).

    Если обрамляющая фигура задана — измерения берутся по ней,
    иначе (только для аморфных областей) — по площади полигона.
    """

    def __init__(self, points: list[QPointF], kind: str,
                 bound: Optional[Shape] = None) -> None:
        super().__init__()
        self.points = [QPointF(p) for p in points]
        self.KIND = kind
        self.bound = bound
        if bound is not None:
            self.OUTLINE_KEY = bound.OUTLINE_KEY

    def _create_items(self, scenes, config) -> None:
        pen = self.pen(config)
        polygon = QPolygonF(self.points)

        def builder(scene):
            return scene.addPolygon(polygon, pen)

        self._add_to_both(scenes, builder)
        if self.bound is not None:
            self.bound.add_to(scenes, config)
            self.items.extend(self.bound.items)

    def move_center_to(self, center: QPointF) -> None:
        raise NotImplementedError("use move_by for polygons")

    def _bound_size_row(self, pixel_proportion: float) -> tuple:
        row = self.bound.size_row(pixel_proportion)
        return (self.KIND, row[0], row[2], row[3])

    def size_row(self, pixel_proportion: float) -> tuple:
        if self.bound is not None:
            return self._bound_size_row(pixel_proportion)
        if self.KIND != "amorphous":
            raise ValueError(f"{self.KIND} requires a bounding figure")
        area = polygon_area(self.points) * pixel_proportion ** 2
        return (self.KIND, None, None, round(area, 3))


class UnitLine(Shape):
    """Единичный отрезок — линейка масштаба. В статистику не входит."""

    KIND = "unit_line"
    OUTLINE_KEY = "unit_line_color"

    def __init__(self, p1: QPointF, p2: QPointF) -> None:
        super().__init__()
        self.p1 = QPointF(p1)
        self.p2 = QPointF(p2)

    @property
    def length(self) -> float:
        dx = self.p1.x() - self.p2.x()
        dy = self.p1.y() - self.p2.y()
        return math.hypot(dx, dy)

    def _create_items(self, scenes, config) -> None:
        pen = QPen(QColor(config.colors[self.OUTLINE_KEY]),
                   config.sizes["unit_line_width"])
        pen.setCosmetic(True)

        def builder(scene):
            return scene.addLine(self.p1.x(), self.p1.y(),
                                 self.p2.x(), self.p2.y(), pen)

        self._add_to_both(scenes, builder)

    def move_center_to(self, center: QPointF) -> None:
        raise NotImplementedError("use move_by")

    def size_row(self, pixel_proportion: float) -> tuple:
        raise ValueError("UnitLine is not part of the statistics")


def polygon_area(points: list[QPointF]) -> float:
    """Площадь простого многоугольника (формула шнурования)."""
    area = 0.0
    for i, p in enumerate(points):
        q = points[(i + 1) % len(points)]
        area += p.x() * q.y() - q.x() * p.y()
    return abs(area) / 2


def perpendicular(v: QPointF) -> QPointF:
    """Единичный вектор, перпендикулярный v."""
    length = math.hypot(v.x(), v.y())
    if length == 0:
        return QPointF(0.0, 0.0)
    return QPointF(-v.y() / length, v.x() / length)


def ellipse_from_axes(axis1: tuple[QPointF, QPointF],
                      axis2: tuple[QPointF, QPointF]) -> Ellipse:
    """Построить эллипс по двум осям (как в исходном редакторе)."""
    a1, a2 = axis1
    b1, b2 = axis2
    v1 = a2 - a1
    v2 = b2 - b1
    center = QPointF((a1.x() + a2.x()) / 2, (a1.y() + a2.y()) / 2)
    radius_a = math.hypot(v1.x(), v1.y()) / 2
    radius_b = math.hypot(v2.x(), v2.y()) / 2
    angle_deg = math.degrees(math.atan2(v1.y(), v1.x()))
    return Ellipse(center, radius_a, radius_b, angle_deg)


def points_to_path(points: list[QPointF]) -> QPainterPath:
    path = QPainterPath()
    if points:
        path.moveTo(points[0])
        for p in points[1:]:
            path.lineTo(p)
    return path


EMPTY_BRUSH = QBrush()
