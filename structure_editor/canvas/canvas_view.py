"""The QGraphicsView used as the editing surface.

A plain view would consume mouse events for panning/selection; this subclass
forwards those events to whichever :class:`SelectionTool` is currently active,
so tools behave like modal state machines without monkeypatching.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView

if TYPE_CHECKING:
    from structure_editor.tools.selection_tool import SelectionTool


class CanvasView(QGraphicsView):
    """A view that routes pointer events to an active markup tool."""

    def __init__(self, scene: QGraphicsScene, active_tool: SelectionTool | None = None) -> None:
        super().__init__(scene)
        self.setRenderHints(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(self.ViewportAnchor.AnchorViewCenter)
        self.setDragMode(self.DragMode.NoDrag)
        self.active_tool = active_tool
        self.controller = None  # set by the main window when a controller exists

    def set_active_tool(self, tool) -> None:
        """Set the tool that receives pointer events (or ``None``)."""
        self.active_tool = tool
        if tool is not None:
            self.setCursor(tool.cursor())

    def mousePressEvent(self, event) -> None:
        if self.active_tool is not None and event.button() == Qt.MouseButton.LeftButton:
            self.active_tool.on_press(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self.active_tool is not None:
            self.active_tool.on_move(event)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self.active_tool is not None and event.button() == Qt.MouseButton.LeftButton:
            self.active_tool.on_release(event)
            return
        super().mouseReleaseEvent(event)
        # In move/pan mode a shape may have been dragged; keep the overlay copy
        # of each shape aligned with the one on the image view.
        if self.controller is not None:
            self.controller.sync_peers()
