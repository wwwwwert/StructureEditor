from __future__ import annotations

from PyQt6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox,
                             QDoubleSpinBox, QFormLayout, QVBoxLayout,
                             QWidget)


class ChoiceDialog(QDialog):
    """Диалог выбора одного варианта из списка."""

    def __init__(self, title: str, options: list[str],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self._combo = QComboBox()
        self._combo.addItems(options)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self._combo)
        layout.addWidget(buttons)

    @classmethod
    def ask(cls, title: str, options: list[str],
            parent: QWidget | None = None) -> str | None:
        """Возвращает выбранный вариант или None при отмене."""
        dialog = cls(title, options, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog._combo.currentText()
        return None


class UnitLengthDialog(QDialog):
    """Диалог ввода длины единичного отрезка и единиц измерения."""

    UNITS = ["millimeters", "micrometers", "nanometers"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Unit line length")
        self.setModal(True)

        self.length_spin = QDoubleSpinBox()
        self.length_spin.setRange(0.0001, 1e9)
        self.length_spin.setDecimals(4)
        self.length_spin.setValue(1.0)
        self.length_spin.setSuffix(" units")

        self.units_combo = QComboBox()
        self.units_combo.addItems(self.UNITS)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        form = QFormLayout()
        form.addRow("Length:", self.length_spin)
        form.addRow("Units:", self.units_combo)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    @classmethod
    def ask(cls, parent: QWidget | None = None) -> tuple[float, str] | None:
        """Возвращает (длина, единицы) или None при отмене."""
        dialog = cls(parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return (dialog.length_spin.value(), dialog.units_combo.currentText())
        return None
