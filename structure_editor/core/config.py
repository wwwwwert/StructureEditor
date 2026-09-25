from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib import resources


@dataclass
class AppConfig:
    """Настройки отображения разметки: цвета и размеры элементов."""

    colors: dict[str, str] = field(default_factory=dict)
    sizes: dict = field(default_factory=dict)

    @classmethod
    def load(cls) -> "AppConfig":
        ref = resources.files("structure_editor.resources").joinpath("config.json")
        data = json.loads(ref.read_text(encoding="utf-8"))
        sizes = data.pop("sizes")
        return cls(colors=data, sizes=sizes)

    @classmethod
    def from_file(cls, path) -> "AppConfig":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        sizes = data.pop("sizes")
        return cls(colors=data, sizes=sizes)

    def dash_pattern(self) -> list[float]:
        dash = self.sizes["dash"]
        return [dash["dash"], dash["space"]]
