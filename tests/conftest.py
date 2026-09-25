"""Переменные окружения должны быть заданы до импорта PyQt6."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
