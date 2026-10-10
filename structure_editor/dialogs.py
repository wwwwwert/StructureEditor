"""Modal dialogs used during markup.

These replace the tkinter ``Toplevel`` dialogs of the original application with
PyQt6 equivalents, all styled through the global QSS theme.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
)

_UNITS = ["mm", "um", "nm"]


def ask_unit_length() -> tuple[float, str] | None:
    """Prompt for a physical length and its unit.

    Returns ``(length, unit)`` or ``None`` if the user cancels.
    """
    dialog = QDialog()
    dialog.setWindowTitle("Set unit line length")
    layout = QVBoxLayout(dialog)

    layout.addWidget(QLabel("Enter the physical length represented"))

    spin = QDoubleSpinBox()
    spin.setRange(0.000001, 1e9)
    spin.setDecimals(4)
    spin.setValue(1.0)

    combo = QComboBox()
    combo.addItems(_UNITS)

    form = QFormLayout()
    form.addRow("Length:", spin)
    form.addRow("Units:", combo)
    layout.addLayout(form)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    result = dialog.exec()
    if result != QDialog.DialogCode.Accepted:
        return None
    return float(spin.value()), str(combo.currentText())


def ask_choice(options: list[str], title: str = "Select option") -> str | None:
    """Prompt the user to pick one of *options* (empty cancels)."""
    dialog = QDialog()
    dialog.setWindowTitle(title)
    layout = QVBoxLayout(dialog)

    combo = QComboBox()
    combo.addItems(options)
    combo.setEditable(False)
    layout.addWidget(combo)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return combo.currentText()


def ask_bounding_figure() -> str | None:
    """Ask how to bound a region: circle, ellipse, or use its own area."""
    return ask_choice(
        ["Use area of figure", "Bound with circle", "Bound with ellipse"],
        title="Choose bounding figure",
    )


def ask_detect_method() -> str | None:
    """Ask which automatic detection algorithm to use."""
    return ask_choice(
        ["DistanceTransform", "Filter2D", "HoughCircles"], title="Choose detection method"
    )


def warn(parent, message: str, title: str = "Warning") -> None:
    """Show a non-fatal warning message box."""
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setWindowTitle(title)
    box.setText(message)
    box.exec()


def confirm(parent, message: str, title: str = "Confirm") -> bool:
    """Ask a yes/no question; returns ``True`` when the user confirms."""
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Question)
    box.setWindowTitle(title)
    box.setText(message)
    yes = box.addButton(QMessageBox.StandardButton.Yes)
    box.addButton(QMessageBox.StandardButton.No)
    box.setDefaultButton(yes)
    box.exec()
    return box.clickedButton() is yes
