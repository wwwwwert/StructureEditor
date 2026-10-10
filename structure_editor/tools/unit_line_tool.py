"""Unit line selection tool.

The unit line anchors a known physical length to a pixel distance, giving the
pixel->physical-units proportion used for all measurements.
"""

from __future__ import annotations

from PyQt6.QtCore import QPointF

from structure_editor.tools.selection_tool import SelectionTool, pen_from


class UnitLineTool(SelectionTool):
    """Drawn as a single drag; reports its pixel length on release."""

    def __init__(self, controller) -> None:
        super().__init__(controller)
        self._start = None
        self._item = None

    def on_press(self, event) -> None:
        x, y = self.scene_point(event)
        self._start = (x, y)
        pen = pen_from(self.config.unit_line_color(), self.config.unit_line_width(), dash=False)
        self._item = self.markup.add_line(
            self.controller.next_tag("unit"), QPointF(x, y), QPointF(x, y), pen
        )

    def on_move(self, event) -> None:
        if self._start is None or self._item is None:
            return
        x, y = self.scene_point(event)
        self._item.setLine(self._start[0], self._start[1], x, y)

    def on_release(self, event) -> None:
        if self._start is None or self._item is None:
            return
        x, y = self.scene_point(event)
        length = ((x - self._start[0]) ** 2 + (y - self._start[1]) ** 2) ** 0.5
        self._item.setLine(self._start[0], self._start[1], x, y)
        tag = self._item.data(0)
        self._start = None
        self._item = None
        if length <= 0:
            return
        self.submit("unit_line", ("unit_line", tag, length))
