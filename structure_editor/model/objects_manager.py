"""Storage and aggregation of markup shapes."""

from __future__ import annotations

from structure_editor.model.shapes import BaseShape, shape_from_specs

# A table row: (structure type, bounding figure, dimension label, physical area).
TableRow = tuple[str, str | None, str, float]


class ObjectsManager:
    """Owns the set of created shapes and turns them into table rows."""

    def __init__(self) -> None:
        self.shapes: dict[str, BaseShape] = {}
        self._line: list[TableRow] = []

    @property
    def created_items(self) -> dict[str, BaseShape]:
        """Alias kept for compatibility; prefer :attr:`shapes`."""
        return self.shapes

    def add(self, kind: str, specs) -> BaseShape | None:
        """Build and store a shape from a drawing-tool result ``specs``."""
        shape = shape_from_specs(kind, specs)
        if shape is not None:
            self.shapes[shape.tag] = shape
        return shape

    def remove(self, tag: str) -> None:
        """Drop the shape identified by *tag*, if present."""
        self.shapes.pop(tag, None)

    def clear(self) -> None:
        """Remove all stored shapes."""
        self.shapes.clear()

    @property
    def count(self) -> int:
        """Number of stored shapes."""
        return len(self.shapes)

    def build_lines(self, pixel_proportion: float) -> list[TableRow]:
        """Compute sorted measurement rows for every stored shape.

        Rows are sorted ascending by physical area so that the histogram and
        table share the same, deterministic order.
        """
        lines: list[TableRow] = []
        for shape in self.shapes.values():
            bounding, label = shape.describe(pixel_proportion)
            area = shape.area(pixel_proportion)
            lines.append((shape.kind, bounding, label, round(area, 3)))
        lines.sort(key=lambda row: row[3])
        self._line = lines
        return lines

    @property
    def lines(self) -> list[TableRow]:
        """Last computed measurement rows (empty until :meth:`build_lines`)."""
        return self._line
