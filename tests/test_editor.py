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


def test_vision_detection_warns_when_missing(window, monkeypatch):
    """If OpenCV is missing, auto-detection warns instead of crashing."""
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
