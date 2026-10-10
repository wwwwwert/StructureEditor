"""Shared pytest fixtures (Qt application + window under test)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest
from PIL import Image
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication

from structure_editor.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    """A single QApplication for the whole test session (headless)."""
    app = QApplication.instance() or QApplication([])
    yield app


def make_sample(path) -> str:
    """Create a small synthetic "structure photo" and return its path.

    A dark background with one bright circular blob so detection/selection
    has something meaningful to work with.
    """
    h, w = 400, 600
    rng = np.random.default_rng(0)
    img = np.full((h, w, 3), 35, dtype=np.uint8)
    cx, cy, radius = 120, 200, 40
    yy, xx = np.mgrid[0:h, 0:w]
    mask = (xx - cx) ** 2 + (yy - cy) ** 2 < radius**2
    img[mask] = (220, 220, 220)
    noise = rng.integers(0, 20, size=(h, w, 1), dtype=np.uint8)
    img = np.clip(img.astype(int) + noise, 0, 255).astype(np.uint8)

    Image.fromarray(img).save(path)
    return path


@pytest.fixture
def sample_path(tmp_path) -> str:
    """Path to a generated sample image."""
    return make_sample(str(tmp_path / "sample.png"))


@pytest.fixture
def window(qapp, sample_path):
    """A fresh MainWindow with an image already loaded."""
    win = MainWindow()
    win.document_name = sample_path
    win.controller.open_image(QPixmap(sample_path))
    yield win
    win.close()
