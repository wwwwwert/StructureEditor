from __future__ import annotations

from PyQt6.QtCore import QObject, QPointF, pyqtSignal
from PyQt6.QtGui import QGuiApplication

from ..core import detection
from ..core.config import AppConfig
from ..core.shapes import Circle, Shape, UnitLine, dashed_pen
from ..core.store import ShapeStore
from .canvas import EditorCanvas
from .tools import PointerTool, Tool


class EditorController(QObject):
    """Связующее звено между холстами, инструментами и хранилищем фигур.

    Один контроллер управляет сразу двумя сценами (фото+разметка и
    только разметка) — дублирование кода рисования исключено.
    """

    tool_changed = pyqtSignal(object)      # Tool | None
    shape_added = pyqtSignal(object)       # Shape
    shapes_changed = pyqtSignal()
    unit_changed = pyqtSignal()

    DETECTORS = {
        "DistanceTransform": detection.find_circles_distance,
        "Filter2D": detection.find_circles_filter2d,
        "HoughCircles": detection.find_circles_hough,
    }

    def __init__(self, config: AppConfig, parent: QObject | None = None):
        super().__init__(parent)
        self.config = config
        self.canvas = EditorCanvas()
        self.canvas.set_controller(self)
        self.store = ShapeStore()

        self.image_path: str | None = None
        self.image_proportion = 1.0
        self.pixel_proportion = 0.0
        self.unit_type: str | None = None

        self._tool: Tool | None = None
        self.activate_default_tool()

    # -- изображение -------------------------------------------------------
    @property
    def image_open(self) -> bool:
        return self.image_path is not None

    @property
    def scenes(self):
        return self.canvas.scenes

    def load_image(self, path: str) -> bool:
        screen = QGuiApplication.primaryScreen()
        size = screen.availableGeometry().size() if screen else None
        screen_w = size.width() if size else 1280
        screen_h = size.height() if size else 800
        max_size = ((screen_w - 60) // 2, screen_h - 70)

        if not self.canvas.load_image(path, max_size):
            return False
        self.image_path = path
        self.image_proportion = self.canvas.image_proportion
        self.store.clear()
        self.pixel_proportion = 0.0
        self.unit_type = None
        self.shapes_changed.emit()
        self.unit_changed.emit()
        return True

    # -- инструменты --------------------------------------------------------
    @property
    def current_tool(self) -> Tool | None:
        return self._tool

    def set_tool(self, tool: Tool | None) -> None:
        if self._tool is not None:
            self._tool.cleanup()
        self._tool = tool
        self.tool_changed.emit(tool)

    def activate_default_tool(self) -> None:
        self.set_tool(PointerTool(self))

    # -- фигуры -------------------------------------------------------------
    def add_shape(self, shape: Shape) -> Shape:
        shape.add_to(self.scenes, self.config)
        self.store.add(shape)
        self.shape_added.emit(shape)
        self.shapes_changed.emit()
        return shape

    def remove_shape(self, shape: Shape) -> None:
        if self.store.by_tag(shape.tag) is None:
            shape.destroy()
            return
        self.store.remove(shape.tag)
        self.shapes_changed.emit()

    def bind_shape(self, shape: Shape, bound: Shape) -> None:
        """Назначить фигуре обрамляющую фигуру (для аморфных областей)."""
        shape.bound = bound
        bound.add_to(self.scenes, self.config)
        shape.items.extend(bound.items)
        self.shapes_changed.emit()

    def clear_markup(self) -> None:
        self.store.clear()
        self.pixel_proportion = 0.0
        self.unit_type = None
        self.shapes_changed.emit()
        self.unit_changed.emit()

    def replace_unit_line(self, unit_line: UnitLine) -> None:
        for shape in self.store.shapes:
            if isinstance(shape, UnitLine):
                self.store.remove(shape.tag)
        self.add_shape(unit_line)
        self.unit_changed.emit()

    # -- масштаб -------------------------------------------------------------
    def set_unit(self, length: float, line_length_px: float,
                 unit_type: str) -> None:
        self.pixel_proportion = length / line_length_px
        self.unit_type = unit_type
        self.unit_changed.emit()

    @property
    def unit_ready(self) -> bool:
        return self.pixel_proportion > 0 and self.unit_type is not None

    # -- детекция -------------------------------------------------------------
    def detect_circles_like(self, method: str, radius_display: float,
                            center_display: QPointF) -> int:
        """Найти окружности с радиусом ±15% от нарисованной."""
        detector = self.DETECTORS[method]
        radius = radius_display / self.image_proportion
        center = (center_display.x() / self.image_proportion,
                  center_display.y() / self.image_proportion)
        circles = detector(self.image_path, radius, center)
        return self._add_detected(circles)

    def detect_all_circles(self, method: str) -> int:
        """Найти все окружности на изображении."""
        detector = self.DETECTORS[method]
        circles = detector(self.image_path)
        return self._add_detected(circles)

    def _add_detected(self, circles) -> int:
        count = 0
        for x, y, radius in circles or []:
            self.add_shape(Circle(
                QPointF(x * self.image_proportion,
                        y * self.image_proportion),
                radius * self.image_proportion))
            count += 1
        return count

    # -- утилиты --------------------------------------------------------------
    def tools_dashed_pen(self, color_key: str):
        return dashed_pen(self.config, color_key)
