# Structure Editor — developer notes

PyQt6 program for microstructure photograph analysis. A full rewrite of the
original Tkinter app; nothing depends on the old root-level scripts.

## Run / test

```bash
uv sync --extra vision          # install (with automatic detection support)
QT_QPA_PLATFORM=offscreen uv run pytest
uv run structure-editor         # launch the GUI
```

## Architecture

- `model/` — UI-agnostic shape model. `BaseShape` is the base class; `Circle`,
  `Ellipse`, `Region` (`Polygon`, `Amorphous`) are subclasses. `ObjectsManager`
  stores shapes and computes sorted measurement rows.
- `canvas/` — one `QGraphicsScene` holds both the image layer and the markup
  overlay (`MarkupScene`). `CanvasController` is the single object that writes
  to both, so the two layers stay in sync. `CanvasView` forwards pointer events
  to the active tool.
- `tools/` — `SelectionTool` base + concrete tools (circle, ellipse, polygon,
  freehand, unit line). Each is a mouse-event state machine calling
  `submit(kind, specs)`. `auto_detect.py` wraps OpenCV behind a lazy import.
- `analysis/` — Plotly histogram + pandas table + exporters.
- `main_window.py` — menu/toolbar/tabs; wires tools to the canvas and model.

## Dependency policy

Heavy/optional packages (OpenCV, scikit-image, scipy, tqdm) live in the
`vision` extra and are imported lazily. `auto_detect.is_available()` gates the
feature; the UI warns if it is missing. Keep new hard dependencies out of the
base group.

## Testing conventions

- Tests run headless with `QT_QPA_PLATFORM=offscreen` and `pytest-qt`.
- Mouse gestures are simulated by sending events to `view.viewport()` with
  coordinates obtained from `view.mapFromScene(...)` (see `tests/test_editor.py`).
- Plot-image rendering (kaleido) needs a browser; tests stub `_show_plot` and
  exercise the figure/data/CSV/PNG path instead.