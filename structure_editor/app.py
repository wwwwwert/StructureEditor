"""Application bootstrap for the structure editor."""

from __future__ import annotations

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from structure_editor.main_window import MainWindow
from structure_editor.theme import load_theme


def _apply_palette(app: QApplication) -> None:
    """Push a dark Material palette so no widget is left system-white.

    QSS styling has gaps (table corner, splitter handles, some reaches of the
    tab bar); an application-wide palette guarantees a uniform dark background
    everywhere and keeps text/selection readable.
    """
    bg = QColor("#1e222b")
    surface = QColor("#232936")
    surface_high = QColor("#2c3340")
    on_bg = QColor("#e6e9ef")
    on_surface = QColor("#aab3c0")
    accent = QColor("#bb86fc")
    disabled = QColor("#6a7280")

    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, bg)
    pal.setColor(QPalette.ColorRole.WindowText, on_bg)
    pal.setColor(QPalette.ColorRole.Base, surface)
    pal.setColor(QPalette.ColorRole.AlternateBase, surface_high)
    pal.setColor(QPalette.ColorRole.Text, on_bg)
    pal.setColor(QPalette.ColorRole.PlaceholderText, on_surface)
    pal.setColor(QPalette.ColorRole.Button, surface)
    pal.setColor(QPalette.ColorRole.ButtonText, on_bg)
    pal.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.white)
    pal.setColor(QPalette.ColorRole.Highlight, accent)
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#121212"))
    pal.setColor(QPalette.ColorRole.ToolTipBase, surface_high)
    pal.setColor(QPalette.ColorRole.ToolTipText, on_bg)
    pal.setColor(QPalette.ColorRole.Link, accent)
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled)
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled)
    app.setPalette(pal)


def configure_application(app: QApplication) -> None:
    """Apply the palette and stylesheet to an existing QApplication.

    Keeping this separate from :func:`create_application` lets tests host a
    window on a QApplication that is themed exactly like the real one, so
    styling behaviour is exercised rather than an unthemed default.
    """
    _apply_palette(app)
    app.setStyleSheet(load_theme())


def create_application(argv=None) -> QApplication:
    """Create and configure the QApplication with the dark Material theme."""
    # Allow fractional / per-display DPI so vector icons stay crisp.
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("Structure Editor")
    app.setOrganizationName("StructureEditor")
    configure_application(app)
    return app


def run(argv=None) -> int:
    """Launch the application and return the process exit code."""
    app = create_application(argv)
    window = MainWindow()
    window.show()
    return app.exec()
