from __future__ import annotations

import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (QFileDialog, QLabel, QMainWindow, QMessageBox,
                             QTabWidget, QToolBar)

from ..core import detection
from ..core.config import AppConfig
from .dialogs import ChoiceDialog
from .editor import EditorController
from .stats import TableView, PlotView, build_stats_widgets
from .tools import (CircleDetectTool, CircleTool, DETECT_METHODS_ALL,
                    EllipseTool, FreehandTool, MoveTool, PolyhedronTool,
                    RemoveTool, UnitLineTool)

IMAGE_FILTER = "Images (*.bmp *.png *.jpg *.jpeg)"


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig | None = None):
        super().__init__()
        self.config = config or AppConfig.load()
        self.editor = EditorController(self.config)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)
        self.setCentralWidget(self.tabs)

        self._welcome_tab = self._build_welcome_tab()
        self.tabs.addTab(self._welcome_tab, "About")

        self.table_view = TableView()
        self.plot_view = PlotView()

        self.setWindowTitle("Structure Editor")
        self.resize(1200, 800)

        self._build_actions()
        self._build_toolbar()
        self._build_menus()
        self._build_status_bar()

        self.editor.tool_changed.connect(self._on_tool_changed)

    # -- вкладки ------------------------------------------------------------
    def _build_welcome_tab(self) -> QLabel:
        label = QLabel(
            "<h2>Structure Editor</h2>"
            "<p>Program for microstructure photographs analysis "
            "and particles dimensions evaluation.</p>"
            "<ol>"
            "<li>Open a structure image (File → Open)</li>"
            "<li>Create markup with tools on the toolbar</li>"
            "<li>Select the unit line</li>"
            "<li>Build and export the histogram "
            "(Statistics → Build graph and table)</li>"
            "</ol>"
            "<p style='color: gray'>by Uspenskiy Dmitry · HSE University, 2022</p>")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setObjectName("welcomeLabel")
        return label

    def _build_status_bar(self) -> None:
        self.status_label = QLabel("Open an image to start")
        self.statusBar().addWidget(self.status_label)
        self.editor.unit_changed.connect(self._update_status)
        self.editor.shapes_changed.connect(self._update_status)

    def _update_status(self) -> None:
        if not self.editor.image_open:
            self.status_label.setText("Open an image to start")
            return
        parts = [f"Objects: {len(self.editor.store)}"]
        if self.editor.unit_ready:
            parts.append(f"Unit: 1 px = "
                         f"{self.editor.pixel_proportion:.4g} "
                         f"{self.editor.unit_type}")
        tool = self.editor.current_tool
        if tool is not None and tool.name != "pointer":
            parts.append(f"Tool: {tool.name.replace('_', ' ')}")
        self.status_label.setText(" · ".join(parts))

    # -- действия -------------------------------------------------------------
    def _build_actions(self) -> None:
        def add(text, shortcut, handler, checkable=False):
            action = QAction(text, self)
            if shortcut:
                action.setShortcut(QKeySequence(shortcut))
            action.setCheckable(checkable)
            action.triggered.connect(handler)
            return action

        self.open_action = add("Open...", "Ctrl+O", self.open_image)
        self.circle_action = add("Circle selection", None,
                                 lambda: self._set_tool(CircleTool),
                                 checkable=True)
        self.circle_detect_action = add(
            "Circle selection with auto-detection", None,
            lambda: self._set_tool(CircleDetectTool), checkable=True)
        self.detect_all_action = add("Select all circles", None,
                                     self.detect_all_circles)
        self.ellipse_action = add("Ellipse selection", None,
                                  lambda: self._set_tool(EllipseTool),
                                  checkable=True)
        self.polyhedron_action = add("Polyhedron selection", None,
                                     lambda: self._set_tool(PolyhedronTool),
                                     checkable=True)
        self.freehand_action = add("Amorphous area selection", None,
                                   lambda: self._set_tool(FreehandTool),
                                   checkable=True)
        self.unit_line_action = add("Select unit line", None,
                                    lambda: self._set_tool(UnitLineTool),
                                    checkable=True)
        self.move_action = add("Move selection", "M",
                               lambda: self._set_tool(MoveTool),
                               checkable=True)
        self.remove_action = add("Remove selection", "R",
                                 lambda: self._set_tool(RemoveTool),
                                 checkable=True)
        self.remove_all_action = add("Remove all", None, self.remove_all)
        self.finish_action = add("Finish polyhedron", "Return",
                                 self._finish_polyhedron)
        self.build_stats_action = add("Build graph and table", "Ctrl+B",
                                      self.build_stats)

        self.tool_actions = [
            self.circle_action, self.circle_detect_action,
            self.ellipse_action, self.polyhedron_action,
            self.freehand_action, self.unit_line_action,
            self.move_action, self.remove_action,
        ]

    def _build_toolbar(self) -> QToolBar:
        toolbar = QToolBar("Tools")
        toolbar.setObjectName("mainToolBar")
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        for action in (self.open_action, None,
                       self.circle_action, self.circle_detect_action,
                       self.detect_all_action, self.ellipse_action,
                       self.polyhedron_action, self.freehand_action,
                       self.unit_line_action, None,
                       self.move_action, self.remove_action,
                       self.remove_all_action, None,
                       self.finish_action, self.build_stats_action):
            if action is None:
                toolbar.addSeparator()
            else:
                toolbar.addAction(action)
        self.finish_action.setVisible(False)
        return toolbar

    def _build_menus(self) -> None:
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        file_menu.addAction(self.open_action)

        selection_menu = menu.addMenu("Selection")
        create_menu = selection_menu.addMenu("Create selection")
        for action in (self.circle_action, self.circle_detect_action,
                       self.detect_all_action, self.ellipse_action,
                       self.polyhedron_action, self.freehand_action,
                       self.unit_line_action):
            create_menu.addAction(action)
        edit_menu = selection_menu.addMenu("Edit selection")
        edit_menu.addAction(self.move_action)
        edit_menu.addAction(self.remove_action)
        edit_menu.addAction(self.remove_all_action)

        stats_menu = menu.addMenu("Statistics")
        stats_menu.addAction(self.build_stats_action)
        save_graph = QAction("Save graph...", self)
        save_graph.triggered.connect(self.plot_view.save_png)
        save_table = QAction("Save table...", self)
        save_table.triggered.connect(self.table_view.save_csv)
        stats_menu.addAction(save_graph)
        stats_menu.addAction(save_table)

    # -- инструменты ------------------------------------------------------------
    def _set_tool(self, tool_factory) -> None:
        if not self._require_image():
            self._uncheck_tools()
            return
        self.editor.set_tool(tool_factory(self.editor))

    def _uncheck_tools(self) -> None:
        for action in self.tool_actions:
            action.setChecked(False)

    def _on_tool_changed(self, tool) -> None:
        self._uncheck_tools()
        self.finish_action.setVisible(bool(tool and tool.has_finish))
        if tool is not None:
            for action in self.tool_actions:
                if action.text().lower().startswith(tool.name.replace("_", " ")):
                    action.setChecked(True)
        self._update_status()

    def _finish_polyhedron(self) -> None:
        tool = self.editor.current_tool
        if isinstance(tool, PolyhedronTool):
            tool.finish()

    # -- файл ---------------------------------------------------------------------
    def open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open structure image",
                                              "", IMAGE_FILTER)
        if not path:
            return

        self._close_image_tabs()
        if not self.editor.load_image(path):
            QMessageBox.warning(self, "Error",
                                f"Cannot open image: {path}")
            return

        self.tabs.addTab(self.editor.canvas, os.path.basename(path))
        self.tabs.setCurrentWidget(self.editor.canvas)

    def _close_image_tabs(self) -> None:
        for view in (self.editor.canvas, self.table_view, self.plot_view):
            index = self.tabs.indexOf(view)
            if index >= 0:
                self.tabs.removeTab(index)

    # -- разметка ------------------------------------------------------------
    def _require_image(self) -> bool:
        if not self.editor.image_open:
            QMessageBox.warning(self, "Warning", "No image opened")
            return False
        return True

    def detect_all_circles(self) -> None:
        if not self._require_image():
            return
        method = ChoiceDialog.ask("Detection method", DETECT_METHODS_ALL,
                                  self)
        if method is None:
            return
        try:
            count = self.editor.detect_all_circles(method)
        except detection.DetectionUnavailableError as exc:
            QMessageBox.warning(self, "Detection unavailable", str(exc))
            return
        except detection.ImageReadError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        if count == 0:
            QMessageBox.information(
                self, "Detection", "No circles found. "
                "Try another method or tune the parameters.")

    def remove_all(self) -> None:
        if not self._require_image() or len(self.editor.store) == 0:
            return
        answer = QMessageBox.question(
            self, "Remove all selection", "Clear all markup?")
        if answer == QMessageBox.StandardButton.Yes:
            self.editor.clear_markup()

    # -- статистика ---------------------------------------------------------------
    def build_stats(self) -> None:
        if not self._require_image():
            return
        if len(self.editor.store) == 0:
            QMessageBox.warning(self, "Warning", "Create markup first")
            return
        if not self.editor.unit_ready:
            QMessageBox.warning(self, "Warning",
                                "Select unit line first")
            return

        self.editor.activate_default_tool()
        try:
            self.table_view, self.plot_view = build_stats_widgets(
                self.editor.store.shapes, self.editor.pixel_proportion,
                self.editor.unit_type)
        except ValueError as exc:
            QMessageBox.warning(
                self, "Export error",
                f"Plotly kaleido is required to render the graph:\n{exc}")
            return

        for view, title in ((self.table_view, "Table"),
                            (self.plot_view, "Plot")):
            index = self.tabs.indexOf(view)
            if index >= 0:
                self.tabs.removeTab(index)
            self.tabs.addTab(view, title)
        self.tabs.setCurrentWidget(self.plot_view)

    # -- клавиатура -----------------------------------------------------------------
    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.editor.activate_default_tool()
            self._uncheck_tools()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._finish_polyhedron()
            return
        super().keyPressEvent(event)
