"""End-to-end tests: image load, manual selection, and result export."""

from __future__ import annotations

import os

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtTest import QTest


def _prepare_view_mapping(window) -> None:
    """Ensure the view shows the scene with an identity transform.

    With the scene smaller than the viewport and scroll bars zeroed, viewport
    coordinates equal scene coordinates, letting QTest target the scene
    directly through the view.
    """
    window.resize(900, 700)
    window.show()
    from PyQt6.QtTest import QTest

    QTest.qWaitForWindowExposed(window.view)
    view = window.view
    view.resetTransform()
    view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    view.horizontalScrollBar().setValue(0)
    view.verticalScrollBar().setValue(0)


def _viewport(window, x, y):
    """Return the viewport coordinates of a scene point, honoring the map."""
    return window.view.mapFromScene(x, y)


def _press(point, window=None):
    view = window.view
    QTest.mousePress(
        view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
    )


def _release(point, window=None):
    view = window.view
    QTest.mouseRelease(
        view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
    )


def _select_circle(window, cx=100, cy=100, radius=40) -> None:
    """Drive the circle tool through a press-drag-release gesture on the view."""
    window._run_tool("circle")
    view = window.view
    p1 = _viewport(window, cx, cy)
    p2 = _viewport(window, cx + radius, cy)
    _press(p1, window)
    QTest.mouseMove(view.viewport(), p2)
    _release(p2, window)


def _select_ellipse(window, cx=100, cy=100, major=40, minor=20) -> None:
    """Drive the ellipse tool: major axis drag, then a perpendicular minor drag.

    The first drag defines the major axis end-to-end; the second defines the
    minor axis, so two press-drag-release pairs are needed to finish it.
    """
    window._run_tool("ellipse")
    view = window.view
    # First phase: major axis from (cx, cy) to (cx + major, cy).
    p1 = _viewport(window, cx, cy)
    p2 = _viewport(window, cx + major, cy)
    _press(p1, window)
    QTest.mouseMove(view.viewport(), p2)
    _release(p2, window)
    # Second phase: minor axis through the center, perpendicular to the major.
    p3 = _viewport(window, cx, cy - minor)
    _press(p2, window)
    QTest.mouseMove(view.viewport(), p3)
    _release(p3, window)


# ----------------------------------------------------------------------
def test_image_loads_into_canvas(window):
    """Opening a document places its pixmap as the scene background."""
    assert window.document_name
    assert window.controller.background_pixmap() is not None
    rect = window.controller.scene.sceneRect()
    assert rect.width() > 0 and rect.height() > 0
    assert QPixmap(window.document_name).isNull() is False


def test_manual_circle_selection_creates_shape(window):
    """A drag with the circle tool adds a shape to the manager."""
    _prepare_view_mapping(window)
    before = window.manager.count
    _select_circle(window, cx=100, cy=100, radius=40)
    assert window.manager.count == before + 1


def test_manual_ellipse_selection_creates_shape(window):
    """The two-drag ellipse gesture adds a shape (regression for the second-phase
    press crash)."""
    _prepare_view_mapping(window)
    before = window.manager.count
    _select_ellipse(window, cx=100, cy=100, major=40, minor=20)
    assert window.manager.count == before + 1


def test_tab_background_is_dark(window):
    """The Editor/Table/Plot tab strip must render dark, never system-white.

    This guards against the native tab bar painting a light background that the
    stylesheet leaves uncovered. It samples the tab strip and checks that the
    dominant colour (the background) is dark, tolerating the lighter grey of the
    inactive tab labels that sit on top.
    """
    import collections

    window.resize(900, 600)
    window.show()
    from PyQt6.QtTest import QTest

    QTest.qWaitForWindowExposed(window.view)
    img = window.tabs.grab().toImage()
    counts = collections.Counter()
    for gx in range(80, 820, 12):
        for gy in range(4, 34, 3):
            counts[img.pixelColor(gx, gy).name()] += 1

    dominant = counts.most_common(1)[0][0] if counts else None
    assert dominant is not None, "could not sample any tab-strip pixels"
    r, g, b = (int(dominant[i : i + 2], 16) for i in (1, 3, 5))
    lum = (r + g + b) / 3
    assert lum < 100, f"dominant tab-strip colour is too light: {dominant} (lum={lum:.0f})"


def _set_unit_line(window) -> None:
    """Draw a horizontal 100 px unit line and answer the length dialog."""
    window._run_tool("unit_line")
    view = window.view
    p1 = _viewport(window, 10, 10)
    p2 = _viewport(window, 110, 10)
    _press(p1, window)
    QTest.mouseMove(view.viewport(), p2)
    _release(p2, window)


def test_unit_line_sets_proportion(window, monkeypatch):
    """Selecting a unit line and entering its length sets the proportion."""
    _prepare_view_mapping(window)
    from structure_editor import dialogs

    monkeypatch.setattr(dialogs, "ask_unit_length", lambda: (100.0, "um"))

    _set_unit_line(window)

    assert window.unit_type == "um"
    # 100 physical over 100 px == 1.0
    assert window.pixel_proportion == pytest.approx(1.0, abs=1e-6)


def test_build_statistics_and_export_table(window, tmp_path, monkeypatch):
    """After a selection + unit line, statistics build and the table exports."""
    _prepare_view_mapping(window)
    from structure_editor import dialogs

    monkeypatch.setattr(dialogs, "ask_unit_length", lambda: (100.0, "um"))
    _select_circle(window, cx=100, cy=100, radius=40)
    _set_unit_line(window)

    # Avoid the live image-render (kaleido/browser) inside the test.
    window._show_plot = lambda: None
    window.build_graph_and_table()
    assert window._figure is not None
    assert window.table_view.model() is not None

    out = str(tmp_path / "table.csv")
    window.manager.build_lines(window.pixel_proportion)
    from structure_editor.analysis import size_table

    size_table.to_csv_path(window.manager, window.unit_type, out)
    assert os.path.exists(out)
    with open(out) as f:
        assert "Structure Type" in f.read()

    # Export markup image.
    img_out = str(tmp_path / "markup.png")
    from structure_editor.analysis import exporter

    exporter.render_scene_to_png(window.controller, img_out, overlay_only=True)
    assert os.path.exists(img_out)


def test_overlay_scene_mirrors_shape(window):
    """A drawn shape appears on both the image scene and the markup-only one."""
    _prepare_view_mapping(window)
    _select_circle(window, cx=100, cy=100, radius=40)
    assert window.manager.count == 1
    image_shapes = [it for it in window.controller.image.scene.items() if it.data(1) == "shape"]
    overlay_shapes = [it for it in window.controller.overlay.scene.items() if it.data(1) == "shape"]
    assert len(image_shapes) == 1
    assert len(overlay_shapes) == 1
    # The overlay copy carries the same tag as the image copy.
    assert image_shapes[0].data(0) == overlay_shapes[0].data(0)


def test_toggle_hides_overlay_view(window):
    """The overlay toggle action shows and hides the markup-only view."""
    window.act_toggle_overlay.setChecked(False)
    window.toggle_overlay_view()
    assert window.overlay_view.isHidden()
    window.act_toggle_overlay.setChecked(True)
    window.toggle_overlay_view()
    assert not window.overlay_view.isHidden()


def test_delete_selected_removes_shape(window):
    """Deleting a selected shape drops it from both scenes and the model."""
    _prepare_view_mapping(window)
    _select_circle(window, cx=100, cy=100, radius=40)
    assert window.manager.count == 1
    item = next(it for it in window.controller.image.scene.items() if it.data(1) == "shape")
    item.setSelected(True)
    window.delete_selected()
    assert window.manager.count == 0
    remaining = [it for it in window.controller.image.scene.items() if it.data(1) == "shape"]
    assert remaining == []


def test_vision_detection_warns_when_missing(window, monkeypatch):
    import structure_editor.tools.auto_detect as ad

    monkeypatch.setattr(ad, "is_available", lambda: False)
    warned = {}

    from structure_editor import dialogs

    def fake_warn(parent, message, title="Warning"):
        warned["message"] = message

    monkeypatch.setattr(dialogs, "warn", fake_warn)

    window.auto_detect_circles()
    assert "vision" in warned.get("message", "").lower()


def test_auto_detection_finds_circles(window, sample_path):
    """When the vision extras are present, detection returns circle tuples."""
    import structure_editor.tools.auto_detect as ad

    if not ad.is_available():
        pytest.skip("vision extras not installed")
    circles = ad.find_circles_distance_transform(sample_path)
    assert isinstance(circles, list)
    for c in circles:
        assert len(c) == 3
        assert all(isinstance(v, (int, float)) for v in c)
