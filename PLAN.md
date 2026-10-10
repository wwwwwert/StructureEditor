# Rewrite Plan — structure-editor (PyQt6)

## Goal
Rewrite the Tkinter-based microstructure photo editor into a modern, maintainable
PyQt6 application with clean architecture, no code duplication, an optional
OpenCV feature-set, and pytest coverage.

## Target architecture (package `structure_editor/`)

```
structure_editor/
  __init__.py
  __main__.py            # python -m structure_editor entrypoint
  app.py                 # QApplication bootstrap, loads QSS theme
  main_window.py         # MainWindow: menu/toolbar, tabs, wires everything
  config.py              # config.json loader + DPI/proportion scaling (from interface_config.py)
  theme/
    __init__.py
    style.qss            # modern dark UI stylesheet
  model/
    __init__.py
    shapes.py            # BaseShape + Circle/Ellipse/Polygon/Amorphous subclasses
    objects_manager.py   # add/remove/iterate shapes (from objects_manager.py)
  canvas/
    __init__.py
    markable_canvas.py   # QGraphicsScene/View: background image
    overlay_canvas.py    # independent overlay for markup (mirror of old dual-canvas)
    canvas_controller.py # ONE object manipulating both canvases (dedup of old drawing_tools)
  tools/
    __init__.py
    selection_tool.py    # base interactive drawing tool (state machine)
    circle_tool.py
    ellipse_tool.py
    polygon_tool.py
    freehand_tool.py     # amorphous area (from drawing_tools.py draw_custom_area)
    unit_line_tool.py
    auto_detect.py       # opencv circle detection (lazy import) (from detecting_circles.py)
  analysis/
    __init__.py
    histogram.py         # plotly histogram + export (replaces matplotlib/seaborn)
    size_table.py        # QTableWidget table (replaces sizes_table.py ttk)
    exporter.py          # save plot/table
  dialogs.py             # length/units, bounding figure, detect-method dialogs
```

## Walkthrough of the user's requested changes

1. **PyQt6 + QSS modern styling**
   - Replace all `tkinter` widgets with QWidgets; QMainWindow + QTabWidget.
   - A hand-written `style.qss` for a dark, modern UI (palette, buttons,
     toolbar, tree/table, dialogs). Keep a small color palette in one place.
2. **uv + fresh Python, lean & trojan-free deps**
   - `pyproject.toml` managed by uv. Base deps: PyQt6, numpy, pandas, plotly,
     shapely, kaleido (plotly image export). All are well-known official
     PyPI packages — no trojans.
   - Heavy/optional deps (opencv-python, scikit-image, scipy, tqdm) moved to
     an optional `vision` extra. Lazy-imported behind a
     `DetectionBackend.available()` check; UI shows a warning dialog if a
     detection tool is chosen while `cv2` is not installed.
3. **Scripts moved from root into `structure_editor/`** package; entrypoint via
   `module` and console script `structure-editor`.
4. **Clean hierarchy + inheritance, no duplication**
   - `BaseShape` with subclasses; shared geometry/area code lives once.
   - `ObjectsManager` stores shapes (not raw tuples), exposes typed accessors.
   - `CanvasController` is the single object that manipulates both the image
     canvas and the overlay canvas (replaces per-tool twin `create_*` calls in
     `drawing_tools.py`).
5. **matplotlib/seaborn → plotly**
   - Histogram built with Plotly Express (histogram per structure type).
   - Export to PNG via kaleido; table rendered with a QTableWidget and
     exported to PNG/CSV.
6. **pytest tests** (headless via `QT_QPA_PLATFORM=offscreen` + `pytest-qt`):
   - Loading an image into the canvas.
   - Manually creating a selection (simulate a drag on an item/view).
   - Exporting the resulting table/plot — assert a file is produced.
7. **Docstrings + comments in English.**
8. **Work in a new git branch and commit.**

## Faithful behaviour preservation (from the old code)

- Markup tools: circle, circle+autodetect, select-all-circles, ellipse,
  polygon, amorphous/freehand, unit line.
- Edit tools: move selection, remove selection, remove all.
- Dual canvases stay in sync: every shape drawn identically on the image
  canvas and its overlay mirror.
- Unit line → pixel↔physical length proportion; histogram + table use it.
- Config colors/sizes applied and scaled to screen DPI.
- Detection methods: DistanceTransform, Filter2D, HoughCircles (auto scene
  detection uses DistanceTransform / HoughCircles).

## Known bugs in the old code worth fixing in the rewrite
- `detecting_circles.py:196` — `maxloc[0] + y` computes x+y → should be
  `maxloc[1] + y` (y-coordinate). Fixed in the new `auto_detect.py`.
- Duplicated `nms`/`nms_indices` and per-tool twin-canvas drawing — unified.

## Open decisions (will default to sensible option if unchecked)
- Move/cancel geometry is handled by per-item item-moveable flags on shapes.
- Default theme: dark; `config.json` keeps color overrides.

## Done when
- `uv run structure-editor` opens a styled window.
- Manual pipeline (load → circle selection → unit line → histogram+table →
  export) works in the offscreen QTest harness and pytest passes.