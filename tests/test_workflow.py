"""Сквозные тесты: загрузка изображения, ручное выделение, выгрузка результата.

GUI-тесты идут в offscreen-платформе Qt (см. conftest.py).
"""
import os
from pathlib import Path

import pytest
from PyQt6.QtCore import QPointF, Qt

from structure_editor.core.config import AppConfig
from structure_editor.ui.main_window import MainWindow
from structure_editor.ui.tools import CircleTool

SAMPLE_IMAGE = Path(__file__).parent.parent / "image_samples" / "test.png"


@pytest.fixture
def window(qtbot):
    win = MainWindow(AppConfig.load())
    qtbot.addWidget(win)
    win.show()
    return win


def _viewport_pos(view, scene_pos: QPointF):
    """Перевести координаты сцены в координаты виджета для событий мыши."""
    return view.mapFromScene(scene_pos)


def test_image_loads(window):
    """Картинка открывается и появляется на обоих холстах."""
    assert window.editor.load_image(str(SAMPLE_IMAGE))

    assert window.editor.image_open
    assert window.editor.image_proportion > 0
    # Изображение — в сцене выделения, в сцене разметки его нет
    selection_items = window.editor.scenes.selection.items()
    markup_items = window.editor.scenes.markup.items()
    assert any(item.pixmap() is not None and not item.pixmap().isNull()
               for item in selection_items)
    assert all(getattr(item, "pixmap", None) is None
               or item.pixmap().isNull() for item in markup_items)


def test_image_load_failure(window):
    """Несуществующий файл отклоняется без падения."""
    assert not window.editor.load_image("/nonexistent/image.png")
    assert not window.editor.image_open


def test_manual_circle_selection(window, qtbot):
    """Круг выделяется «вручную» — событиями мыши на холсте."""
    assert window.editor.load_image(str(SAMPLE_IMAGE))
    view = window.editor.canvas.selection_view

    window.editor.set_tool(CircleTool(window.editor))

    center = QPointF(150, 120)
    edge = QPointF(190, 120)  # радиус 40 px
    qtbot.mousePress(view.viewport(), Qt.MouseButton.LeftButton,
                     pos=_viewport_pos(view, center))
    qtbot.mouseMove(view.viewport(), pos=_viewport_pos(view, edge))
    qtbot.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton,
                       pos=_viewport_pos(view, edge))

    shapes = window.editor.store.shapes
    assert len(shapes) == 1
    circle = shapes[0]
    assert circle.KIND == "circle"
    assert abs(circle.radius - 40) < 1.5
    # Элементы созданы в обеих сценах
    assert len(circle.items) == 2


def test_full_workflow_export(window, qtbot, tmp_path, monkeypatch):
    """Загрузка → ручное выделение → масштаб → статистика → выгрузка."""
    from structure_editor.ui import dialogs
    from structure_editor.ui import stats as stats_module

    assert window.editor.load_image(str(SAMPLE_IMAGE))
    view = window.editor.canvas.selection_view

    # 1. Ручное выделение кругом
    window.editor.set_tool(CircleTool(window.editor))
    qtbot.mousePress(view.viewport(), Qt.MouseButton.LeftButton,
                     pos=_viewport_pos(view, QPointF(150, 120)))
    qtbot.mouseMove(view.viewport(), pos=_viewport_pos(view, QPointF(190, 120)))
    qtbot.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton,
                       pos=_viewport_pos(view, QPointF(190, 120)))

    # 2. Единичный отрезок (диалог подменяем, чтобы не блокировать тест)
    monkeypatch.setattr(dialogs.UnitLengthDialog, "ask",
                        classmethod(lambda cls, parent=None: (2.0, "micrometers")))
    window.editor.set_tool(__import__(
        "structure_editor.ui.tools", fromlist=["UnitLineTool"]).UnitLineTool(
        window.editor))
    qtbot.mousePress(view.viewport(), Qt.MouseButton.LeftButton,
                     pos=_viewport_pos(view, QPointF(50, 300)))
    qtbot.mouseMove(view.viewport(), pos=_viewport_pos(view, QPointF(150, 300)))
    qtbot.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton,
                       pos=_viewport_pos(view, QPointF(150, 300)))
    assert window.editor.unit_ready

    # 3. Статистика через то же API, что использует интерфейс
    table, plot = stats_module.build_stats_widgets(
        window.editor.store.shapes,
        window.editor.pixel_proportion,
        window.editor.unit_type)

    csv_path = tmp_path / "table.csv"
    png_path = tmp_path / "histogram.png"
    html_path = tmp_path / "histogram.html"
    table._df.to_csv(csv_path, index=False)
    plot._figure.write_image(str(png_path))
    plot._figure.write_html(str(html_path))

    # 4. Результат выгружен и непустой
    assert csv_path.exists() and csv_path.stat().st_size > 0
    assert png_path.exists() and png_path.stat().st_size > 0
    assert html_path.exists() and html_path.stat().st_size > 0

    # Данные согласованы: один объект, площадь считается по масштабу
    assert len(table._df) == 1
    row = table._df.iloc[0]
    # радиус 40 px при линейке 2 мкм / 100 px → 0.8 мкм
    assert abs(row["size"] - 3.14159 * 0.8 ** 2) < 0.01
