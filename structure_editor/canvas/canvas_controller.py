"""Canvas controller: single owner of the scene, view and active tool.

This is the object that "manipulates both canvases": the image layer (the
photograph) and the overlay layer (the markup) live in one scene and every
drawing command is issued here, so the two layers can never drift apart.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView

from structure_editor.canvas.markup_scene import MarkupScene
from structure_editor.config import Config


class CanvasController:
    """Owns the QGraphicsScene, the QGraphicsView and the active MarkupScene."""

    def __init__(self, config: Config, view: QGraphicsView | None = None) -> None:
        self.config = config
        self.scene = QGraphicsScene()
        self.markup = MarkupScene(self.scene)
        self.view = view
        self._tag_counter = 0
        if view is not None:
            view.setScene(self.scene)

    def next_tag(self, prefix: str = "shape") -> str:
        """Return a unique markup tag; used as a shape/cluster identifier."""
        self._tag_counter += 1
        return f"{prefix}{self._tag_counter}"

    def clear_markup(self) -> None:
        """Clear all markup while keeping the background image."""
        self.markup.clear_markup()

    def open_image(self, pixmap) -> None:
        """Set the background image and reset the markup layer."""
        self.markup.set_background(pixmap)
        if self.view is not None:
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def background_pixmap(self):
        """Return the current background pixmap item, if any."""
        item = self.markup.background_item
        return item.pixmap() if item is not None else None

    def render_overlay(self, target):
        """Render only the markup overlay into the given painter/target."""
        was = self.markup.background_item.isVisible()
        self.markup.background_item.setVisible(False)
        try:
            self.scene.render(target)
        finally:
            self.markup.background_item.setVisible(was)

    def render_full(self, target):
        """Render the whole composed scene (image + markup)."""
        self.scene.render(target)
