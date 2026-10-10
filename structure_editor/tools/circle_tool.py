"""Circle selection tool."""

from __future__ import annotations

import math

from PyQt6.QtCore import QPointF

from structure_editor.tools.selection_tool import SelectionTool, pen_from


class CircleTool(SelectionTool):
    """Draw a circle by pressing at its center and dragging to its border."""

    def __init__(self, controller) -> None:
        super().__init__(controller)
        self.center: QPointF | None = None
        self._preview = None
        self._radius = 0.0

    def on_press(self, event) -> None:
        x, y = self.scene_point(event)
        self.center = QPointF(x, y)
        self._radius = 0.0
        self._preview = self.markup.add_oval(
            self.controller.next_tag("preview"), self.center, 0.0, self._pen()
        )

    def on_move(self, event) -> None:
        if self.center is None:
            return
        cx, cy = self.scene_point(event)
        self._radius = math.hypot(cx - self.center.x(), cy - self.center.y())
        self._resize_preview(self._radius)

    def on_release(self, event) -> None:
        if self.center is None:
            return
        radius = self._radius
        # Promote the preview circle to a real, tagged shape.
        tag = self.controller.next_tag("shape")
        final = self.markup.add_oval(tag, self.center, radius, self._pen())
        if self._preview is not None:
            self.scene.removeItem(self._preview)
            self._preview = None
        self.center = None
        final_radius = final.rect().width() / 2.0
        cx = final.sceneBoundingRect().center().x()
        cy = final.sceneBoundingRect().center().y()
        if final_radius <= 0:
            return
        self.submit("circle", ("circle", tag, final_radius, cx, cy))

    def _pen(self):
        return pen_from(self.config.render_color(), self.config.line_width())

    def _resize_preview(self, radius: float) -> None:
        if self._preview is None:
            return
        rect = self._preview.rect()
        rect.setLeft(self.center.x() - radius)
        rect.setTop(self.center.y() - radius)
        rect.setWidth(radius * 2)
        rect.setHeight(radius * 2)
        self._preview.setRect(rect)
