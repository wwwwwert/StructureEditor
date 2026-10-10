"""Ellipse selection tool."""

from __future__ import annotations

import math

from PyQt6.QtCore import QPointF

from structure_editor.tools.selection_tool import SelectionTool, pen_from


class EllipseTool(SelectionTool):
    """Draw an ellipse from two perpendicular axes.

    First drag draws the major axis from end to end; the subsequent drag draws
    the minor axis which is forced to run through the center perpendicular to
    the first.
    """

    def __init__(self, controller) -> None:
        super().__init__(controller)
        self.first_axis: tuple = (0, 0, 0, 0)
        self.second_axis: tuple = (0, 0, 0, 0)
        self._phase = "first"  # "first" -> "second"
        self._start = (0.0, 0.0)
        self._preview = None
        self._axes = []

    def on_press(self, event) -> None:
        self._start = self.scene_point(event)
        if self._phase == "first":
            x, y = self._start
            self.first_axis = (x, y, x, y)
        else:
            x1, y1, x2, y2 = self.first_axis
            self.second_axis = (x, y, x, y)

    def on_move(self, event) -> None:
        x, y = self.scene_point(event)
        if self._phase == "first":
            self._update_axis(self.first_axis, x, y)
        else:
            self._update_second(x, y)

    def on_release(self, event) -> None:
        if self._phase == "first":
            self._phase = "second"
        else:
            self._finish()

    def _update_axis(self, axis, x, y):
        axis = (axis[0], axis[1], x, y)
        if self._phase == "first":
            self.first_axis = axis
            self._draw_axis_line(axis)

    def _update_second(self, x, y):
        x1, y1, x2, y2 = self.first_axis
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        dx, dy = x1 - x2, y1 - y2
        length = math.hypot(x - cx, y - cy)
        # Perpendicular unit vector to the first axis.
        if math.hypot(dx, dy) == 0:
            ux, uy = 0.0, 1.0
        else:
            ux, uy = -dy / math.hypot(dx, dy), dx / math.hypot(dx, dy)
        endx, endy = cx + ux * length, cy + uy * length
        self.second_axis = (cx - ux * length, cy - uy * length, endx, endy)
        self._draw_axis_line(self.second_axis)

    def _draw_axis_line(self, axis):
        if self._axes:
            old = self._axes.pop(0)
            self.scene.removeItem(old)
            self._axes = []
        x1, y1, x2, y2 = axis
        pen = pen_from(self.config.colors.get("axle_color", "#e6c229"), self.config.line_width())
        item = self.markup.add_line("", QPointF(x1, y1), QPointF(x2, y2), pen)
        self._axes.append(item)

    def _finish(self) -> None:
        # Clean up temporary axis guides.
        for item in self._axes:
            self.scene.removeItem(item)
        self._axes = []

        x1, y1, x2, y2 = self.first_axis
        a = math.hypot(x2 - x1, y2 - y1) / 2
        x3, y3, x4, y4 = self.second_axis
        b = math.hypot(x4 - x3, y4 - y3) / 2

        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        tag = self.controller.next_tag("shape")
        pen = pen_from(self.config.colors.get("oval_color", "#ffa726"), self.config.line_width())
        # Build the ellipse as a cosmetic rect centered on the midpoints.
        self.markup.add_ellipse(tag, cx, cy, a, b, pen)
        self._phase = "first"
        if a > 0 and b > 0:
            self.submit("ellipse", ("ellipse", tag, a, b))
