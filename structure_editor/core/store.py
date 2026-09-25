from __future__ import annotations

from .shapes import Shape


class ShapeStore:
    """Хранилище фигур разметки. Вся работа с фигурами идёт через него,
    чтобы сцены оставались согласованными."""

    def __init__(self) -> None:
        self._shapes: dict[str, Shape] = {}

    def add(self, shape: Shape) -> Shape:
        self._shapes[shape.tag] = shape
        return shape

    def remove(self, tag: str) -> None:
        shape = self._shapes.pop(tag)
        shape.destroy()

    def clear(self) -> None:
        for shape in list(self._shapes.values()):
            shape.destroy()
        self._shapes.clear()

    def by_tag(self, tag: str) -> Shape | None:
        return self._shapes.get(tag)

    @property
    def shapes(self) -> list[Shape]:
        return list(self._shapes.values())

    def __len__(self) -> int:
        return len(self._shapes)
