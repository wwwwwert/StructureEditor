"""Application bootstrap for the structure editor."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from structure_editor.main_window import MainWindow
from structure_editor.theme import load_theme


def create_application(argv=None) -> QApplication:
    """Create and configure the QApplication with the QSS theme applied."""
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("Structure Editor")
    app.setOrganizationName("StructureEditor")
    app.setStyleSheet(load_theme())
    return app


def run(argv=None) -> int:
    """Launch the application and return the process exit code."""
    app = create_application(argv)
    window = MainWindow()
    window.show()
    return app.exec()
