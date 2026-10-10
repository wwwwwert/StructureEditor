"""Canvas controller: single owner of the two scenes, their views and the tool.

This is the object that "manipulates two canvases at once": one scene shows the
photograph with the markup on top, ``image``, the other shows only the markup
over a plain background, ``overlay``. Every drawing command is routed through
here, so the two views can never drift apart.
"""

from __future__ import annotations

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QPen, QPixmap
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView

from structure_editor.canvas.markup_scene import MarkupScene
from structure_editor.config import Config


class CanvasController:
    """Owns two synchronized :class:`MarkupScene` objects, their views and tags.

    * ``image``    -- the photo with the markup overlay.
    * ``overlay``  -- only the markup, no photo (used for a clean overlay view).

    Each drawing operation targets *both* scenes with identical coordinates and
    the same unique tag, and records which overlay item mirrors each image item,
    so cleanup and removal stay consistent.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.scene = QGraphicsScene()
        self.image = MarkupScene("image", self.scene)
        self.overlay = MarkupScene("overlay", QGraphicsScene())
        self.view: QGraphicsView | None = None  # primary (image+markup) view
        self.overlay_view: QGraphicsView | None = None  # markup-only view
        self._tag_counter = 0
        # image_item -> overlay_item mirror, used for symmetric removal.
        self._peers: dict = {}

    # ------------------------------------------------------------- tags
    def next_tag(self, prefix: str = "shape") -> str:
        """Return a unique markup tag that is shared by both views."""
        self._tag_counter += 1
        return f"{prefix}{self._tag_counter}"

    # ------------------------------------------------------- drawing API
    def add_oval(self, tag: str, center: QPointF, radius: float, pen: QPen):
        """Draw a circle on both canvases; returns the image-scene item."""
        img = self.image.add_oval(tag, center, radius, pen)
        ov = self.overlay.add_oval(tag, center, radius, pen)
        self._peers[img] = ov
        return img

    def add_line(self, tag: str, p1: QPointF, p2: QPointF, pen: QPen):
        """Draw a line on both canvases; returns the image-scene item."""
        img = self.image.add_line(tag, p1, p2, pen)
        ov = self.overlay.add_line(tag, p1, p2, pen)
        self._peers[img] = ov
        return img

    def add_ellipse(self, tag, cx, cy, radius_a, radius_b, pen):
        """Draw an ellipse on both canvases; returns the image-scene item."""
        img = self.image.add_ellipse(tag, cx, cy, radius_a, radius_b, pen)
        ov = self.overlay.add_ellipse(tag, cx, cy, radius_a, radius_b, pen)
        self._peers[img] = ov
        return img

    def add_path_shape(self, path_item) -> None:
        """Add a finished shape on the image scene and mirror it to the overlay."""
        self.image.scene.addItem(path_item)
        self.mirror_to_overlay(path_item)

    def add_polygon_shape(self, polygon_item) -> None:
        """Add a finished polygon on the image scene and mirror it to the overlay."""
        self.image.scene.addItem(polygon_item)
        self.mirror_to_overlay(polygon_item)

    def mirror_to_overlay(self, image_item) -> None:
        """Mirror an already-placed shape item to the overlay scene."""
        if image_item is None or image_item in self._peers:
            return
        clone = self._clone_item(image_item)
        self.overlay.scene.addItem(clone)
        self._peers[image_item] = clone

    def _clone_item(self, item):
        """Build a standalone twin of *item* so both canvases look identical."""
        from PyQt6.QtWidgets import (
            QGraphicsEllipseItem,
            QGraphicsLineItem,
            QGraphicsPathItem,
            QGraphicsPolygonItem,
        )

        if isinstance(item, QGraphicsEllipseItem):
            clone = QGraphicsEllipseItem(item.rect())
        elif isinstance(item, QGraphicsLineItem):
            clone = QGraphicsLineItem(item.line())
        elif isinstance(item, QGraphicsPolygonItem):
            clone = QGraphicsPolygonItem(item.polygon())
        elif isinstance(item, QGraphicsPathItem):
            clone = QGraphicsPathItem(item.path())
        else:  # pragma: no cover - unknown shape; draw nothing on the overlay
            return None
        clone.setPen(item.pen())
        clone.setBrush(item.brush())
        clone.setZValue(item.zValue())
        clone.setData(0, item.data(0))
        clone.setData(1, item.data(1))
        from PyQt6.QtWidgets import QGraphicsItem

        clone.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        clone.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        return clone

    def remove_item(self, image_item) -> None:
        """Remove a shape from *both* scenes by mirror identity."""
        if image_item is None:
            return
        peer = self._peers.pop(image_item, None)
        if peer is not None and peer.scene() is self.overlay.scene:
            self.overlay.scene.removeItem(peer)
        if image_item.scene() is self.image.scene:
            self.image.scene.removeItem(image_item)

    def remove_by_tag(self, tag) -> None:
        """Remove every shape (both scenes) whose tag equals *tag*."""
        if not tag:
            return
        for img in list(self._peers.keys()):
            if img.data(0) == tag:
                self.remove_item(img)

    def sync_peers(self) -> None:
        """Copy image-item positions to the overlay so dragging stays in sync."""
        for img, ov in self._peers.items():
            if img is None or ov is None:
                continue
            ov.setPos(img.pos())
            ov.setTransform(img.transform())

    # ------------------------------------------------------- lifecycle
    def open_image(self, pixmap: QPixmap) -> None:
        """Set the background photo on the image scene and reset everywhere."""
        self.image.set_background(pixmap)
        self.overlay.set_background_plain(pixmap.width(), pixmap.height())
        w, h = pixmap.width(), pixmap.height()
        self.image.scene.setSceneRect(0, 0, w, h)
        self.overlay.scene.setSceneRect(0, 0, w, h)
        if self.view is not None:
            self.view.fitInView(self.image.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        if self.overlay_view is not None:
            self.overlay_view.fitInView(
                self.overlay.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio
            )

    def clear_markup(self) -> None:
        """Clear markup on both canvases while keeping the image."""
        self.image.clear_markup()
        self.overlay.clear_markup()
        self._peers.clear()

    def background_pixmap(self):
        """Return the current background photo, if any."""
        item = self.image.background_item
        return item.pixmap() if item is not None else None

    # ------------------------------------------------------- rendering
    def render_overlay(self, target) -> None:
        """Render only the overlay (no photo) into a painter/target."""
        self.overlay.scene.render(target)

    def render_full(self, target) -> None:
        """Render the composed image + markup into a painter/target."""
        self.image.scene.render(target)
