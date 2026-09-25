from __future__ import annotations

import sys
from importlib import resources

from PyQt6.QtWidgets import QApplication

from .core.config import AppConfig
from .ui.main_window import MainWindow


def load_stylesheet(app: QApplication) -> None:
    try:
        ref = resources.files("structure_editor.resources").joinpath(
            "styles.qss")
        app.setStyleSheet(ref.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError):
        pass  # QSS опционален, приложение работает и без него


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Structure Editor")
    app.setOrganizationName("HSE")
    load_stylesheet(app)

    window = MainWindow(AppConfig.load())
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
