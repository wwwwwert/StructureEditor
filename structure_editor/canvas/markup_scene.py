"""The graphics scene that hosts the background image and markup overlay."""

from __future__ import annotations

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPen, QPixmap
from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QGraphicsLineItem

from structure_editor.model.shapes import SHAPE_TAG


class MarkupScene:
    """A scene combined of an image layer and an overlay markup layer.

    Instead of the original two sibling canvases, the background photograph
    is a pixmap item at the bottom of one scene while all markup items live
    above it. The overlay can be exported alone by hiding the image layer.
    """

    def __init__(self, name: str, scene) -> None:
        self.name = name
        # ``scene`` is a QGraphicsScene the controller owns; kept here so the
        # controller and the tools share the exact same reference.
        self._scene = scene
        self.background_item = None  # QGraphicsPixmapItem

    @property
    def scene(self):
        """The underlying QGraphicsScene."""
        return self._scene

    def set_background(self, pixmap: QPixmap) -> None:
        """Place *pixmap* as the scene background and clear existing markup."""
        self.clear_markup()
        if self.background_item is not None:
            self._scene.removeItem(self.background_item)
        self.background_item = self._scene.addPixmap(pixmap)
        self.background_item.setZValue(-1000)
        self._scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())

    def set_background_plain(self, width: int, height: int) -> None:
        """Give the overlay scene a neutral background with no photograph."""
        self.clear_markup()
        if self.background_item is not None:
            self._scene.removeItem(self.background_item)
            self.background_item = None
        self._scene.setSceneRect(0, 0, width, height)

    def clear_markup(self) -> None:
        """Remove every markup item while keeping the background image."""
        for item in list(self._scene.items()):
            if item is self.background_item:
                continue
            self._scene.removeItem(item)

    def add_oval(self, tag: str, center: QPointF, radius: float, pen: QPen) -> QGraphicsEllipseItem:
        """Add a circle markup item to the overlay layer."""
        item = QGraphicsEllipseItem(
            center.x() - radius, center.y() - radius, radius * 2, radius * 2
        )
        self._configure(item, tag, pen)
        return item

    def add_line(self, tag: str, p1: QPointF, p2: QPointF, pen: QPen) -> QGraphicsLineItem:
        """Add a line markup item to the overlay layer."""
        item = QGraphicsLineItem(p1.x(), p1.y(), p2.x(), p2.y())
        self._configure(item, tag, pen)
        return item

    def add_ellipse(
        self, tag: str, cx: float, cy: float, radius_a: float, radius_b: float, pen: QPen
    ) -> QGraphicsEllipseItem:
        """Add an ellipse markup item centered at ``(cx, cy)``."""
        item = QGraphicsEllipseItem(cx - radius_a, cy - radius_b, radius_a * 2, radius_b * 2)
        self._configure(item, tag, pen)
        return item

    def _configure(self, item: QGraphicsItem, tag: str, pen: QPen) -> None:
        item.setPen(pen)
        item.setZValue(0)
        item.setData(0, tag)
        item.setData(1, SHAPE_TAG)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self._scene.addItem(item)

    def items(self):
        """Iterate over markup items (excluding the background)."""
        for item in self._scene.items():
            if item is not self.background_item:
                yield item

    def remove_markup_item(self, item: QGraphicsItem) -> None:
        """Remove one markup item from the scene."""
        if item is not None and item.scene() is self._scene:
            self._scene.removeItem(item)
