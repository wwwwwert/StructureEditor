"""Rendering of markup and results to image/CSV files."""

from __future__ import annotations

from PyQt6.QtGui import QImage, QPainter

from structure_editor.canvas.canvas_controller import CanvasController


def render_scene_to_png(
    controller: CanvasController, path: str, overlay_only: bool = False
) -> None:
    """Render the composed scene (or just its overlay) to a PNG at *path*."""
    rect = controller.scene.sceneRect()
    image = QImage(int(rect.width()), int(rect.height()), QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    if overlay_only:
        controller.render_overlay(painter)
    else:
        controller.render_full(painter)
    painter.end()
    image.save(path, "PNG")
