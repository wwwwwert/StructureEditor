"""Main window: menu, toolbar, splitter, tabs, and wiring of tools to the canvas.

The editor page holds two synchronized views in a splitter:

* the left **image view** composites the photograph with the markup,
* the right **overlay view** shows only the markup on a neutral background and
  can be shown or hidden with a toolbar toggle.
"""

from __future__ import annotations

import contextlib
from pathlib import Path

from PyQt6.QtCore import QPointF, QSize, Qt
from PyQt6.QtGui import QAction, QKeySequence, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QSplitter,
    QTableView,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from structure_editor import dialogs
from structure_editor.analysis import exporter, histogram, size_table
from structure_editor.canvas.canvas_controller import CanvasController
from structure_editor.canvas.canvas_view import CanvasView
from structure_editor.config import Config, default_config_path
from structure_editor.model.objects_manager import ObjectsManager
from structure_editor.tools import auto_detect
from structure_editor.tools.circle_tool import CircleTool
from structure_editor.tools.ellipse_tool import EllipseTool
from structure_editor.tools.freehand_tool import FreehandTool
from structure_editor.tools.polygon_tool import PolygonTool
from structure_editor.tools.selection_tool import pen_from
from structure_editor.tools.unit_line_tool import UnitLineTool

_IMAGE_FILTER = "Images (*.png *.bmp *.jpg *.jpeg)"
_DRAW_TOOLS = ("circle", "ellipse", "polygon", "freehand")


class MainWindow(QMainWindow):
    """The application's primary window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Structure Editor")
        self.resize(1200, 800)

        # Configuration and screen-relative sizing.
        screen = self.screen() if self.screen() else None
        width = screen.size().width() if screen else 1280
        height = screen.size().height() if screen else 800
        self.config = Config(default_config_path(), width, height)

        # Model + controller.
        self.controller = CanvasController(self.config)
        self.manager = ObjectsManager()
        self.document_name = ""

        # Semantic measurement state.
        self.unit_type: str | None = None
        self.pixel_proportion: float = 0.0
        self._figure = None

        # Views + tool registry.
        self.view: CanvasView | None = None
        self.overlay_view: CanvasView | None = None
        self._tools = {}
        self._active_tool = None

        self._build_ui()
        self._build_menus_and_toolbar()
        self._build_icons()
        self._update_action_states()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        self.tabs = QTabWidget(self)
        # Keep the standard (non-document) tab style: document mode can make the
        # tab strip render with a native light background that QSS cannot paint.
        self.tabs.setDocumentMode(False)

        self.editor_page = QWidget()
        lay = QVBoxLayout(self.editor_page)
        lay.setContentsMargins(0, 0, 0, 0)

        # Two synchronized views: photo+markup (left) and markup-only (right).
        self.view = CanvasView(self.controller.scene, active_tool=None)
        self.view.controller = self.controller
        self.controller.view = self.view

        self.overlay_view = CanvasView(self.controller.overlay.scene, active_tool=None)
        self.overlay_view.controller = self.controller
        self.controller.overlay_view = self.overlay_view

        self._splitter = QSplitter(Qt.Orientation.Horizontal, self.editor_page)
        self._splitter.addWidget(self.view)
        self._splitter.addWidget(self.overlay_view)
        self._splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])
        self._splitter.setChildrenCollapsible(False)
        lay.addWidget(self._splitter, 1)

        self.status_label = QLabel("Open an image to begin.")
        self.status_label.setContentsMargins(8, 4, 8, 4)
        lay.addWidget(self.status_label)

        self.table_page = QWidget()
        self.table_view = QTableView(self.table_page)
        table_lay = QVBoxLayout(self.table_page)
        table_lay.setContentsMargins(0, 0, 0, 0)
        table_lay.addWidget(self.table_view)

        self.plot_page = QWidget()
        plot_lay = QVBoxLayout(self.plot_page)
        plot_lay.setContentsMargins(0, 0, 0, 0)
        self.plot_placeholder = QLabel("Build a graph to see the histogram here.")
        self.plot_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plot_lay.addWidget(self.plot_placeholder)

        self.tabs.addTab(self.editor_page, "Editor")
        self.tabs.addTab(self.table_page, "Table")
        self.tabs.addTab(self.plot_page, "Plot")
        self.setCentralWidget(self.tabs)

    def _build_icons(self) -> None:
        """Assign crisp vector Material icons to every action.

        Icons are rendered at runtime from embedded SVG paths (``icons.py``) and
        tinted with the theme accent, so the toolbar stays sharp on any display
        and never falls back to low-resolution system icons.
        """
        from structure_editor import icons

        surface = icons.on_surface()
        mapping = {
            self.act_open: "image",
            self.act_export: "download",
            self.act_unit_line: "straighten",
            self.act_circle: "circle",
            self.act_ellipse: "ellipse",
            self.act_polygon: "hexagon",
            self.act_freehand: "draw",
            self.act_detect: "radar",
            self.act_move: "pan_tool",
            self.act_delete_selected: "close",
            self.act_remove_all: "delete",
            self.act_build: "bar_chart",
            self.act_toggle_overlay: "layers",
        }
        for act, name in mapping.items():
            act.setIcon(icons.make(name, surface))

    def _build_menus_and_toolbar(self) -> None:
        self._build_file_menu()
        self._build_selection_menu()
        self._build_stats_menu()
        self._build_toolbar()

    # ------------------------------------------------------------- menus
    def _build_file_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        self.act_open = QAction("Open image...", self)
        self.act_open.setShortcut(QKeySequence.StandardKey.Open)
        self.act_open.triggered.connect(self.open_image)
        file_menu.addAction(self.act_open)

        file_menu.addSeparator()
        self.act_export = QAction("Export markup as PNG", self)
        self.act_export.triggered.connect(self.export_markup)
        file_menu.addAction(self.act_export)

        act_quit = QAction("Quit", self)
        act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

    def _build_selection_menu(self) -> None:
        selection_menu = self.menuBar().addMenu("&Selection")

        self.act_circle = QAction("Circle selection", self, checkable=True)
        self.act_circle.triggered.connect(lambda: self._activate("circle"))
        selection_menu.addAction(self.act_circle)

        self.act_ellipse = QAction("Ellipse selection", self, checkable=True)
        self.act_ellipse.triggered.connect(lambda: self._activate("ellipse"))
        selection_menu.addAction(self.act_ellipse)

        self.act_polygon = QAction("Polyhedron selection", self, checkable=True)
        self.act_polygon.triggered.connect(lambda: self._activate("polygon"))
        selection_menu.addAction(self.act_polygon)

        self.act_freehand = QAction("Amorphous selection", self, checkable=True)
        self.act_freehand.triggered.connect(lambda: self._activate("freehand"))
        selection_menu.addAction(self.act_freehand)

        self.act_detect = QAction("Circle auto-detection", self, checkable=True)
        self.act_detect.triggered.connect(self.auto_detect_circles)
        selection_menu.addAction(self.act_detect)

        selection_menu.addSeparator()
        self.act_unit_line = QAction("Select unit line", self, checkable=True)
        self.act_unit_line.triggered.connect(self.select_unit_line)
        selection_menu.addAction(self.act_unit_line)

        edit_menu = selection_menu.addMenu("Edit selection")
        self.act_move = QAction("Move/select markup", self, checkable=True)
        self.act_move.triggered.connect(self.activate_move)
        edit_menu.addAction(self.act_move)

        self.act_delete_selected = QAction("Delete selected", self)
        self.act_delete_selected.setShortcut(QKeySequence.StandardKey.Delete)
        self.act_delete_selected.triggered.connect(self.delete_selected)
        edit_menu.addAction(self.act_delete_selected)

        self.act_remove_all = QAction("Remove all", self)
        self.act_remove_all.triggered.connect(self.remove_all_selection)
        edit_menu.addAction(self.act_remove_all)

    def _build_stats_menu(self) -> None:
        stats_menu = self.menuBar().addMenu("&Statistics")
        self.act_build = QAction("Build graph & table", self)
        self.act_build.triggered.connect(self.build_graph_and_table)
        stats_menu.addAction(self.act_build)

        self.act_save_graph = QAction("Save graph", self)
        self.act_save_graph.triggered.connect(self.save_graph)
        stats_menu.addAction(self.act_save_graph)

        self.act_save_table = QAction("Save table", self)
        self.act_save_table.triggered.connect(self.save_table)
        stats_menu.addAction(self.act_save_table)

        stats_menu.addSeparator()
        self.act_toggle_overlay = QAction("Show markup-only view", self, checkable=True)
        self.act_toggle_overlay.setChecked(True)
        self.act_toggle_overlay.triggered.connect(self.toggle_overlay_view)
        stats_menu.addAction(self.act_toggle_overlay)

    # ---------------------------------------------------------- toolbar
    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Tools", self)
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(toolbar)

        toolbar.addAction(self.act_open)
        toolbar.addSeparator()

        # Calibration
        self.act_unit_line.setToolTip("Calibrate pixels to a known physical length")
        toolbar.addAction(self.act_unit_line)
        toolbar.addSeparator()

        # Drawing tools
        toolbar.addAction(self.act_circle)
        toolbar.addAction(self.act_ellipse)
        toolbar.addAction(self.act_polygon)
        toolbar.addAction(self.act_freehand)
        toolbar.addAction(self.act_detect)
        toolbar.addSeparator()

        # Edit actions
        self.act_move.setToolTip("Drag shapes around or click to select them")
        toolbar.addAction(self.act_move)
        toolbar.addAction(self.act_delete_selected)
        toolbar.addAction(self.act_remove_all)
        toolbar.addSeparator()

        toolbar.addAction(self.act_build)

    # ------------------------------------------------------------- tools
    def _make_tool(self, name: str):
        factory = {
            "circle": CircleTool,
            "ellipse": EllipseTool,
            "polygon": PolygonTool,
            "freehand": FreehandTool,
            "unit_line": UnitLineTool,
        }[name]
        tool = factory(self.controller)
        tool.begin(self._on_shape_finished)
        return tool

    def _activate(self, name: str) -> None:
        if not self.document_name:
            dialogs.warn(self, "Open an image first.")
            self._uncheck_actions(_DRAW_TOOLS)
            return
        for key, act in self._selection_actions().items():
            if key != name:
                act.setChecked(False)
        self.act_move.setChecked(False)
        self.act_unit_line.setChecked(False)
        self._run_tool(name)

    def _selection_actions(self):
        return {
            "circle": self.act_circle,
            "ellipse": self.act_ellipse,
            "polygon": self.act_polygon,
            "freehand": self.act_freehand,
        }

    def _uncheck_actions(self, keys) -> None:
        for k in keys:
            self._selection_actions()[k].setChecked(False)

    def _run_tool(self, name: str) -> None:
        # Finish any active tool first.
        if self._active_tool is not None:
            with contextlib.suppress(Exception):
                self._active_tool.end()
            self._active_tool = None
            self._tools.clear()
        tool = self._make_tool(name)
        self._active_tool = tool
        self.view.set_active_tool(tool)

    def _on_shape_finished(self, kind: str, specs: tuple) -> None:
        if kind == "unit_line":
            self._on_unit_line(specs)
            return
        self.manager.add(kind, specs)
        self._update_action_states()

    # ------------------------------------------------------- edit actions
    def activate_move(self) -> None:
        """Enter move/select mode: no tool intercepts pointer events, so
        movable markup items can be dragged and selected with the defaults."""
        self.act_move.setChecked(True)
        self._uncheck_actions(_DRAW_TOOLS)
        self.act_unit_line.setChecked(False)
        self.view.set_active_tool(None)

    def delete_selected(self) -> None:
        """Remove every currently selected shape from the model and canvas."""
        removed = False
        for item in list(self.controller.image.scene.selectedItems()):
            tag = item.data(0)
            if not tag:
                continue
            self.manager.remove(tag)
            self.controller.remove_item(item)
            self.controller.remove_by_tag(tag)
            removed = True
        if removed:
            self._update_action_states()

    def remove_all_selection(self) -> None:
        if not self.manager.count:
            return
        if not dialogs.confirm(self, "Clear all markup?", "Remove all selection"):
            return
        self.manager.clear()
        self.controller.clear_markup()
        self._update_action_states()

    def toggle_overlay_view(self) -> None:
        """Show or hide the markup-only view in the editor splitter."""
        self.overlay_view.setVisible(self.act_toggle_overlay.isChecked())

    # ----------------------------------------------------------- actions
    def open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open structure image", "", _IMAGE_FILTER)
        if not path:
            return
        pixmap = QPixmap(path)
        if pixmap.isNull():
            dialogs.warn(self, f"Could not load image: {path}")
            return
        self.controller.open_image(pixmap)
        self.document_name = path
        self.manager.clear()
        self.unit_type = None
        self.pixel_proportion = 0.0
        self._figure = None
        self.status_label.setText(f"Loaded: {Path(path).name}")
        self._update_action_states()

    def _on_unit_line(self, specs) -> None:
        """Prompt for the physical length and store the pixel proportion."""
        result = dialogs.ask_unit_length()
        if result is None:
            return
        length, unit = result
        _kind, _tag, pixels = specs
        if pixels == 0:
            return
        self.pixel_proportion = float(length) / float(pixels)
        self.unit_type = unit
        self.status_label.setText(f"Unit: {length} {unit}  |  pixel = {self.pixel_proportion:.6g}")
        self._update_action_states()

    def select_unit_line(self) -> None:
        if not self.document_name:
            dialogs.warn(self, "Open an image first.")
            self.act_unit_line.setChecked(False)
            return
        self._uncheck_actions(_DRAW_TOOLS)
        self.act_move.setChecked(False)
        self._run_tool("unit_line")

    def auto_detect_circles(self) -> None:
        self.act_detect.setChecked(False)
        if not self.document_name:
            dialogs.warn(self, "Open an image first.")
            return
        if not auto_detect.is_available():
            dialogs.warn(self, auto_detect.missing_message(), "Vision dependencies missing")
            return
        method = dialogs.ask_detect_method()
        if method is None:
            return
        try:
            circles = auto_detect.find_circles_distance_transform(self.document_name)
        except Exception as exc:  # pragma: no cover
            dialogs.warn(self, str(exc), "Detection failed")
            return
        pen = pen_from(self.config.render_color(), self.config.line_width())
        for x, y, r in circles:
            tag = self.controller.next_tag("shape")
            self.controller.add_oval(tag, QPointF(x, y), r, pen)
            self.manager.add("circle", ("circle", tag, r, x, y))
        self._update_action_states()

    # ------------------------------------------------------- statistics
    def build_graph_and_table(self) -> None:
        if not self.document_name:
            dialogs.warn(self, "Open an image first.")
            return
        if self.manager.count == 0:
            dialogs.warn(self, "Create markup first.")
            return
        if self.pixel_proportion == 0 or self.unit_type is None:
            dialogs.warn(self, "Select a unit line first.")
            return
        self.manager.build_lines(self.pixel_proportion)
        self._build_table()
        try:
            self._figure = histogram.build_figure(
                self.manager, self.unit_type, self.pixel_proportion
            )
        except ValueError as exc:
            dialogs.warn(self, str(exc))
            return
        try:
            self._show_plot()
        except Exception as exc:  # e.g. kaleido without a browser to render via
            dialogs.warn(self, f"Could not display the graph: {exc}")
            return
        self.tabs.setCurrentWidget(self.plot_page)

    def _build_table(self) -> None:
        from PyQt6.QtGui import QStandardItem, QStandardItemModel

        df = size_table.to_dataframe(self.manager, self.unit_type)
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(list(df.columns))
        for _, row in df.iterrows():
            items = [QStandardItem(str(v)) for v in row]
            model.appendRow(items)
        self.table_view.setModel(model)
        self.table_view.resizeColumnsToContents()

    def _show_plot(self) -> None:
        """Render the current plotly figure to an image and display it."""
        import os
        import tempfile

        from PyQt6.QtWidgets import QLabel

        fd, tmp = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        try:
            self._figure.write_image(tmp, format="png")
            pix = QPixmap(tmp)
        finally:
            os.remove(tmp)

        layout = self.plot_page.layout()
        if self.plot_placeholder is not None:
            layout.removeWidget(self.plot_placeholder)
            self.plot_placeholder.deleteLater()
            self.plot_placeholder = None
        label = QLabel()
        label.setPixmap(pix)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def save_graph(self) -> None:
        if self._figure is None:
            dialogs.warn(self, "Build the graph first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save graph", "", "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)"
        )
        if not path:
            return
        try:
            self._figure.write_image(path)
        except Exception as exc:  # pragma: no cover
            dialogs.warn(self, f"Could not save graph: {exc}")

    def save_table(self) -> None:
        if self.table_view.model() is None:
            dialogs.warn(self, "Build the table first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save table", "", "CSV (*.csv)")
        if not path:
            return
        size_table.to_csv_path(self.manager, self.unit_type, path)

    def export_markup(self) -> None:
        if not self.document_name:
            dialogs.warn(self, "Open an image first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export markup", "", "PNG (*.png)")
        if not path:
            return
        exporter.render_scene_to_png(self.controller, path, overlay_only=False)

    # ------------------------------------------------------------ state
    def _update_action_states(self) -> None:
        has_image = bool(self.document_name)
        for act in (
            self.act_circle,
            self.act_ellipse,
            self.act_polygon,
            self.act_freehand,
            self.act_detect,
            self.act_unit_line,
            self.act_move,
            self.act_delete_selected,
            self.act_remove_all,
        ):
            act.setEnabled(has_image)
        self.act_build.setEnabled(has_image)
        self.act_export.setEnabled(has_image)
