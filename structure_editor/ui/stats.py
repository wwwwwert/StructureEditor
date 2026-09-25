from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QMessageBox,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget)

from ..core.statistics import (build_histogram, export_histogram_html,
                               export_histogram_png, measurements_dataframe)


class TableView(QWidget):
    """Таблица измерений с экспортом в CSV."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.table = QTableWidget()
        save_button = QPushButton("Save CSV...")
        save_button.setObjectName("accentButton")
        save_button.clicked.connect(self.save_csv)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        layout.addWidget(save_button, alignment=Qt.AlignmentFlag.AlignRight)

        self._df = None

    def set_dataframe(self, df) -> None:
        self._df = df
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(list(df.columns))
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        for row in range(len(df)):
            for col in range(len(df.columns)):
                value = df.iat[row, col]
                text = "" if value is None or str(value) == "None" \
                    else str(value)
                self.table.setItem(row, col, QTableWidgetItem(text))
        self.table.resizeColumnsToContents()

    def save_csv(self) -> None:
        if self._df is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save table", "", "CSV files (*.csv)")
        if path:
            if not path.endswith(".csv"):
                path += ".csv"
            self._df.to_csv(path, index=False)


class PlotView(QWidget):
    """Гистограмма распределения размеров (plotly → PNG) с экспортом."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure_label = QLabel("Build statistics to see the histogram")
        self.figure_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.figure_label.setMinimumSize(600, 450)

        self._figure = None

        png_button = QPushButton("Save PNG...")
        html_button = QPushButton("Export interactive HTML...")
        png_button.clicked.connect(self.save_png)
        html_button.clicked.connect(self.save_html)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(png_button)
        buttons.addWidget(html_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.figure_label, stretch=1)
        layout.addLayout(buttons)

    def set_figure(self, figure, png_bytes: bytes) -> None:
        self._figure = figure
        pixmap = QPixmap()
        pixmap.loadFromData(png_bytes)
        self.figure_label.setPixmap(pixmap)

    def _require_figure(self) -> bool:
        if self._figure is None:
            QMessageBox.warning(self, "Warning",
                                "Build the graph first.")
            return False
        return True

    def save_png(self) -> None:
        if not self._require_figure():
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save graph", "", "PNG images (*.png)")
        if path:
            if not path.endswith(".png"):
                path += ".png"
            try:
                export_histogram_png(self._figure, path)
            except ValueError as exc:
                QMessageBox.warning(self, "Export error", str(exc))

    def save_html(self) -> None:
        if not self._require_figure():
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export graph", "", "HTML files (*.html)")
        if path:
            if not path.endswith(".html"):
                path += ".html"
            export_histogram_html(self._figure, path)


def build_stats_widgets(shapes, pixel_proportion: float,
                        unit_type: str) -> tuple[TableView, PlotView]:
    """Построить таблицу и гистограмму по всем фигурам разметки."""
    df = measurements_dataframe(shapes, pixel_proportion)
    figure = build_histogram(df, unit_type)
    png_bytes = figure.to_image(format="png", scale=2)

    table = TableView()
    table.set_dataframe(df)
    plot = PlotView()
    plot.set_figure(figure, png_bytes)
    return table, plot
