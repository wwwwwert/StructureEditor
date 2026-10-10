# Structure Editor

**Program for microstructure photographs analysis and particles dimensions evaluation.**

A modern PyQt6 rewrite of an earlier Tkinter application. It lets you open a
microstructure photograph, mark up the structures with a selection tool, define
a unit line, and produce a histogram and measurement table of their sizes.

## Features

- **Modern PyQt6 UI** styled with QSS (dark theme).
- Markup tools: **circle**, **ellipse**, **polyhedron**, **amorphous/freehand**
  and **unit line** selection.
- Automatic circle detection (OpenCV) via Distance-Transform, Filter2D and
  HoughCircles — available only when the optional *vision* extras are installed.
- **Plotly** histogram (replaces matplotlib/seaborn) and a measurement table
  with CSV/PNG export.
- Pixel → physical-unit proportion from a user-defined unit line.

## Install

The project is managed with [uv](https://docs.astral.sh/uv/).

```bash
uv sync                      # base dependencies (PyQt6, plotly, numpy, ...)
```

To enable automatic circle detection (needs OpenCV and friends):

```bash
uv sync --extra vision
```

Development / test dependencies:

```bash
uv sync --extra dev --extra vision
```

Run the application:

```bash
uv run structure-editor     # or: uv run python -m structure_editor
```

> **Graph export requires a browser.** Plotly's image export (`kaleido`) needs a
> Chromium/Chrome install on the machine. If it is missing the app shows a
> warning instead of crashing; the histogram display and table/markup export
> still work.

## Usage

1. **File → Open image** to load a structure photograph.
2. Pick a markup tool from the toolbar/menu and draw over structures.
3. **Selection → Select unit line**, then draw a line and enter its real length
   and unit.
4. **Statistics → Build graph & table** to see the histogram and the table.
5. **Statistics → Save graph / Save table** to export the histogram (PNG) or
   table (CSV).

## Project layout

```
structure_editor/
  app.py                 # QApplication bootstrap + QSS theme
  main_window.py         # menu, toolbar, tabs; wires tools to the canvas
  config.py              # config.json + DPI proportion scaling
  dialogs.py             # modal dialogs (length/units, bounding figure, ...)
  theme/style.qss        # dark stylesheet
  model/                 # shapes (inheritance) + objects manager
  canvas/                # scene, view, controller (one object for both layers)
  tools/                 # interactive selection tools + auto-detection
  analysis/              # plotly histogram, table, exporters
tests/                   # pytest + pytest-qt (headless)
```

The canvas is a single `QGraphicsScene` with an image layer underneath a markup
layer. `CanvasController` is the one object that manipulates both, so they can
never drift apart; each selection is a typed `BaseShape` subclass.

## Tests

```bash
QT_QPA_PLATFORM=offscreen uv run pytest
```

Covered: image loading, a manual circle selection, and export of the results
(the plot figure, the table CSV and the markup PNG).