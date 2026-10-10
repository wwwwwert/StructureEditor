"""Entry point for ``python -m structure_editor``."""

from __future__ import annotations

import sys

from structure_editor.app import run


def main() -> int:
    """Launch the application."""
    return run(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
