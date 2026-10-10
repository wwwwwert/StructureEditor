"""Base interactive selection tool.

A tool is a short-lived state machine activated from the menu/toolbar. While
active it receives pointer events forwarded by the :class:`CanvasView`; when a
shape is finished it calls ``submit(kind, specs)`` so the owner can store it.
"""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

from structure_editor.canvas.canvas_controller import CanvasController


class SelectionTool:
    """Base class for markup drawing tools.

    Subclasses override ``on_press`` / ``on_move`` / ``on_release`` and call
    ``submit(kind, specs)`` once the markup is complete.
    """

    def __init__(self, controller: CanvasController) -> None:
        self.controller = controller
        self.scene = controller.scene
        self.markup = controller.markup
        self.config = controller.config
        self._on_finished: Callable[[str, tuple], None] | None = None

    def cursor(self) -> QCursor:
        """The pointer shape used while this tool is active."""
        return QCursor(Qt.CursorShape.CrossCursor)

    def begin(self, on_finished: Callable[[str, tuple], None] | None = None) -> None:
        """Register a completion callback (the view is already wired to us)."""
        self._on_finished = on_finished

    def end(self) -> None:
        """Deactivate the tool and clear any partial markup."""
        self._on_finished = None

    def submit(self, kind: str, specs: tuple) -> None:
        """Finalize a shape; *specs* follows the original tuple conventions."""
        if self._on_finished is not None:
            self._on_finished(kind, specs)

    @property
    def pen(self):
        """Default pen used for ordinary markup items."""
        width = self.config.line_width()
        color = self.config.render_color()
        pen = pen_from(color, width)
        return pen

    def scene_point(self, event) -> tuple[float, float]:
        """Return the scene coordinates of a pointer *event* as ``(x, y)``.

        Works for both ``QMouseEvent`` (mapped through the view) and
        ``QGraphicsSceneMouseEvent`` (which carries scene coordinates already).
        """
        view = self.controller.view
        sc = getattr(event, "scenePosition", None)
        if sc is not None and view is None:
            return sc.x(), sc.y()
        pos = event.position().toPoint()
        if view is not None:
            scene = view.mapToScene(pos)
            return scene.x(), scene.y()
        return pos.x(), pos.y()


def pen_from(color: str, width: int, dash: bool = True):
    """Build a cosmetic QPen with an optional dashed style."""
    from PyQt6.QtGui import QColor, QPen

    pen = QPen(QColor(color))
    pen.setWidthF(width)
    pen.setCosmetic(True)
    if dash:
        pen.setDashPattern([6.0, 4.0])
    return pen
