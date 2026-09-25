# Structure Editor
**Program for microstructure photographs analysis and particles dimensions evaluation**

Desktop application (PyQt6) for marking up structures on microstructure photos,
measuring their sizes using a unit line, and building size-distribution
histograms.

## Requirements

- Python 3.11+ (managed automatically by [uv](https://docs.astral.sh/uv/))
- System Qt/OpenGL runtime libraries (`libegl1` and friends on Linux)

## Setup & run

```Shell
uv sync            # create venv and install dependencies
uv run structure-editor
```

## Tests

```Shell
uv sync --extra dev
uv run pytest
```

GUI tests run on Qt's offscreen platform (`QT_QPA_PLATFORM=offscreen`,
set automatically in `tests/conftest.py`).

## Usage

1. Run `uv run structure-editor`
2. Open a structure image (File → Open)
3. Create markup with the toolbar tools
4. Select the unit line and enter its real length
5. Build and export the histogram and the table (Statistics → Build graph and table)

## Interface

The main window has a toolbar with all markup tools, tabs for the image,
the measurements table and the histogram, plus a status bar showing the
current tool, object count and scale.

Two synced canvases are shown side by side: the photo with markup and the
pure markup layer.

## Markup tools

1. **Circle selection** — press at the structure's center and drag to its border.
2. **Circle selection with auto-detection** — mark one circle and the program
   detects all circles with ±15% radius (DistanceTransform / Filter2D / HoughCircles).
3. **Select all circles** — detect circles of all radii at once.
4. **Ellipse selection** — drag the first axis, then drag the second axis;
   it is drawn perpendicular through the middle automatically.
5. **Polyhedron selection** — draw edges from vertex to vertex (close points
   snap to existing vertices). Press **Finish** (or Enter) and choose the
   bounding figure (circle or ellipse); its parameters are used in the table.
6. **Amorphous selection** — draw a boundary freehand, then either use the
   hand-drawn area or bound it with a circle/ellipse.
7. **Select unit line** — draw a line over the scale bar and enter its length
   and units.

## Project layout

```
structure_editor/
├── app.py               # entry point (QApplication + QSS)
├── core/                # UI-independent logic
│   ├── config.py        # colors/sizes from resources/config.json
│   ├── shapes.py        # Shape base class + Circle/Ellipse/PolygonShape/UnitLine
│   ├── store.py         # ShapeStore — shape lifecycle
│   ├── detection.py     # OpenCV circle detection (distance transform, Filter2D, Hough)
│   └── statistics.py    # measurements table + plotly histogram
├── ui/
│   ├── main_window.py   # window, toolbar, menus, tabs
│   ├── editor.py        # EditorController — one object for both canvases
│   ├── canvas.py        # paired scenes/views (photo+markup, pure markup)
│   ├── tools.py         # tool state machines (circle, ellipse, polyhedron, ...)
│   ├── dialogs.py       # unit length / choice dialogs
│   └── stats.py         # table & plot views with export
└── resources/
    ├── config.json
    └── styles.qss       # dark theme
tests/                   # pytest + pytest-qt (offscreen)
```

Each `Shape` owns mirror items in **both** scenes at once — drawing, moving and
deleting a figure never requires duplicated per-canvas code. Adding a new tool
means subclassing `Tool` and implementing a few mouse handlers.

## Statistics & export

The histogram is built with [plotly](https://plotly.com/python/) and can be
exported as:

- **PNG** (via kaleido) — from the Plot tab or Statistics → Save graph
- **interactive HTML** — from the Plot tab
- **CSV** — from the Table tab or Statistics → Save table

## Automatic marking methods

* **DistanceTransform** — for touching/overlapping circles in flat pictures
  ([OpenCV tutorial](https://docs.opencv.org/4.x/d2/dbd/tutorial_distance_transform.html)).
* **Filter2D** — for non-flat (spherical) structures in noisy pictures with
  shadows ([Filter2D tutorial](https://docs.opencv.org/3.4/d4/dbd/tutorial_filter_2d.html)).
* **HoughCircles** — for simple scenes
  ([Hough circle tutorial](https://docs.opencv.org/3.4/d4/d70/tutorial_hough_circle.html)).

## Creating .exe / .app files

Use [PyInstaller](https://pyinstaller.org/en/stable/):

```Shell
uv run pyinstaller --clean --onefile --windowed \
    --add-data 'structure_editor/resources:structure_editor/resources' \
    -n 'Structure Editor' -m structure_editor.app
```

## License and Registration
Program is registered with the Federal Service
on Intellectual Property
[Registration form RU 2022663303](https://new.fips.ru/registers-doc-view/fips_servlet?DB=EVM&DocNumber=2022663303&TypeFile=html)
