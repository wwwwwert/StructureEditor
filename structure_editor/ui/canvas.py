from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QMouseEvent, QPainter, QPixmap
from PyQt6.QtWidgets import (QGraphicsScene, QGraphicsView, QHBoxLayout,
                             QLabel, QVBoxLayout, QWidget)


class ScenePair:
    """Пара сцен: выделение (изображение + разметка) и разметка (только
    разметка). Фигуры создают зеркальные элементы в обеих."""

    def __init__(self) -> None:
        self.selection = QGraphicsScene()
        self.markup = QGraphicsScene()

    @property
    def both(self) -> tuple[QGraphicsScene, QGraphicsScene]:
        return (self.selection, self.markup)

    def clear(self) -> None:
        self.selection.clear()
        self.markup.clear()


class EditorView(QGraphicsView):
    """Просмотр сцены, пересылающий события мыши активному инструменту."""

    def __init__(self, scene: QGraphicsScene, controller,
                 interactive: bool = True) -> None:
        super().__init__(scene)
        self.controller = controller
        self.interactive = interactive
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setBackgroundBrush(Qt.GlobalColor.darkGray)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setMouseTracking(False)

    # -- маршрутизация событий инструменту --------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:
        tool = self.controller.current_tool if self.controller else None
        if self.interactive and tool is not None:
            tool.on_press(self, event)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        tool = self.controller.current_tool if self.controller else None
        if self.interactive and tool is not None:
            tool.on_move(self, event)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        tool = self.controller.current_tool if self.controller else None
        if self.interactive and tool is not None:
            tool.on_release(self, event)
            event.accept()
            return
        super().mouseReleaseEvent(event)


class EditorCanvas(QWidget):
    """Два синхронных холста: слева фото с разметкой, справа — чистая
    разметка (для выгрузки/просмотра без фона)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.scenes = ScenePair()
        self._controller = None

        self.selection_view = EditorView(self.scenes.selection,
                                         self._controller, interactive=True)
        self.markup_view = EditorView(self.scenes.markup,
                                      self._controller, interactive=False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top = QHBoxLayout()
        top.setSpacing(0)
        top.addWidget(self._header("Photo + markup"))
        top.addWidget(self._header("Markup"))
        layout.addLayout(top)

        views = QHBoxLayout()
        views.setSpacing(0)
        views.addWidget(self.selection_view)
        views.addWidget(self.markup_view)
        layout.addLayout(views, stretch=1)

        self.image_proportion = 1.0
        self._pixmap_item = None

    @staticmethod
    def _header(text: str) -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName("canvasHeader")
        return label

    def set_controller(self, controller) -> None:
        self._controller = controller
        self.selection_view.controller = controller
        self.markup_view.controller = controller

    def load_image(self, path: str, max_size: tuple[int, int]) -> bool:
        """Загрузить изображение, масштабировать под доступный размер.
        Возвращает False при ошибке чтения."""
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return False

        original = pixmap.size()
        scaled = pixmap.scaled(max_size[0], max_size[1],
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        self.image_proportion = (scaled.width() / original.width()
                                 if original.width() else 1.0)

        self.scenes.clear()
        rect = QRectF(0, 0, scaled.width(), scaled.height())
        self._pixmap_item = self.scenes.selection.addPixmap(scaled)
        self._pixmap_item.setZValue(-10)
        for scene in self.scenes.both:
            scene.setSceneRect(rect)
        return True
