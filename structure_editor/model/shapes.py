"""Shape model: a base class plus concrete markup shapes.

Shapes hold the semantic data behind the markup and know how to turn their
geometry into numeric measurements (areas) once a pixels->physical-units
proportion is known. Rendering lives in the canvas/tools layers; this module
is UI-agnostic.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod

# A degree-of-freedom tag shared by all shapes to make them selectable/movable.
SHAPE_TAG = "shape"


class BaseShape(ABC):
    """Common behaviour shared by every markup figure."""

    def __init__(self, tag: str) -> None:
        # ``tag`` is a unique id used to address the drawn items on the canvas.
        self.tag = tag

    @property
    @abstractmethod
    def kind(self) -> str:
        """Human-readable shape type, used for histogram/table grouping."""
        raise NotImplementedError

    @abstractmethod
    def area_in_pixels(self) -> float:
        """Return the shape's area measured in image pixels (before scale)."""
        raise NotImplementedError

    @abstractmethod
    def describe(self, pixel_proportion: float) -> tuple[str | None, str]:
        """Return ``(bounding_figure, dimension_label)`` in physical units.

        ``dimension_label`` is a string such as ``"12.5"`` for a circle or
        ``"12.5\\t8.0"`` for an ellipse whose two radii are tab-separated.
        """
        raise NotImplementedError

    def area(self, pixel_proportion: float) -> float:
        """Return the shape's physical area for a given pixel scale."""
        return self.area_in_pixels() * (pixel_proportion**2)


class Circle(BaseShape):
    """A circular selection described by a center and a radius."""

    def __init__(self, tag: str, x: float, y: float, radius: float) -> None:
        super().__init__(tag)
        self.x = x
        self.y = y
        self.radius = radius

    @property
    def kind(self) -> str:
        return "circle"

    def area_in_pixels(self) -> float:
        return math.pi * self.radius**2

    def describe(self, pixel_proportion: float) -> tuple[str | None, str]:
        radius = self.radius * pixel_proportion
        return None, f"{radius:.3f}"


class Ellipse(BaseShape):
    """An elliptical selection described by two perpendicular radii."""

    def __init__(self, tag: str, radius_a: float, radius_b: float) -> None:
        super().__init__(tag)
        self.radius_a = radius_a
        self.radius_b = radius_b

    @property
    def kind(self) -> str:
        return "ellipse"

    def area_in_pixels(self) -> float:
        return math.pi * self.radius_a * self.radius_b

    def describe(self, pixel_proportion: float) -> tuple[str | None, str]:
        a = self.radius_a * pixel_proportion
        b = self.radius_b * pixel_proportion
        return None, f"{a:.3f}\t{b:.3f}"


class Region(BaseShape):
    """A polygonal region (polyhedron or amorphous) that is measured either
    directly from its own area or through a surrounding circle/ellipse."""

    def __init__(
        self,
        tag: str,
        area: float,
        bounding: str | None = None,
        radius_a: float | None = None,
        radius_b: float | None = None,
    ) -> None:
        super().__init__(tag)
        self.area = area  # only used when bounding is None
        self.bounding = bounding  # None | "circle" | "ellipse"
        self.radius_a = radius_a
        self.radius_b = radius_b

    def area_in_pixels(self) -> float:
        if self.bounding is None:
            return self.area
        if self.bounding == "circle":
            return math.pi * self.radius_a**2
        return math.pi * self.radius_a * self.radius_b

    def describe(self, pixel_proportion: float) -> tuple[str | None, str]:
        if self.bounding is None:
            return None, ""
        if self.bounding == "circle":
            return "circle", f"{self.radius_a * pixel_proportion:.3f}"
        a = self.radius_a * pixel_proportion
        b = self.radius_b * pixel_proportion
        return "ellipse", f"{a:.3f}\t{b:.3f}"


class Polygon(Region):
    """A polyhedron selection measured by area or a bounding figure."""

    @property
    def kind(self) -> str:
        return "polyhedron"


class Amorphous(Region):
    """A freehand-drawn region measured by area or a bounding figure."""

    @property
    def kind(self) -> str:
        return "amorphous"


def shape_from_specs(kind: str, specs) -> BaseShape | None:
    """Factory: rebuild a shape from a drawing-tool result tuple.

    ``specs`` for a region is ``(kind, tag, bounding, ra, rb)`` where, when
    ``bounding`` is ``None``, ``ra`` carries the direct pixel area and ``rb``
    is unused.
    """
    if kind == "circle":
        _k, tag, radius, x, y = specs
        return Circle(tag, x, y, radius)
    if kind == "ellipse":
        _k, tag, ra, rb = specs
        return Ellipse(tag, ra, rb)
    if kind in ("polyhedron", "amorphous"):
        _k, tag, bounding, ra, rb = specs
        if bounding is None:
            return Polygon(tag, area=ra) if kind == "polyhedron" else Amorphous(tag, area=ra)
        if bounding == "circle":
            cls = Polygon if kind == "polyhedron" else Amorphous
            return cls(tag, area=0.0, bounding=bounding, radius_a=ra)
        cls = Polygon if kind == "polyhedron" else Amorphous
        return cls(tag, area=0.0, bounding=bounding, radius_a=ra, radius_b=rb)
    return None
