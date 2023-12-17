
# Structure Editor
**Program for microstructure photographs analysis and particles dimensions evaluation**

# Usage

1. Run structure_editor.py
2. Open structure image
3. Create markup
4. Build and export histogram

# Interface

Program has classic window with all tools in Top Menu. 

Use "File" -> "Open" to select structure image. Only one image can be opened at a time.

Markup Tools are available at "Selection" -> "Create Selection" section.

After creating markup you can edit it with tools from "Selection" -> "Edit Selection" section.

When markup is done and unit line is selected use "Statistics" -> "Build Graph and Table" to create histogram and table with structures discription.

Use "Statistics" -> "Save graph" to export histogram in *.png *.bmp *.jpg *.jpeg formats.

Use "Statistics" -> "Save table" to export table in *.png *.csv formats.

You can navigate between pages by selecting tab on the top.  

# Markup tools

1. "Circle selection". <br> Use this tool to select circle shaped structures like spheres. Press at structure's center and drag the circle to the border. 

2. "Circle selection with outodetection". <br> Use this tool to select one circle and program will detect all circles with +-15% radius.

3. "Select all circles". <br> This tool selects circles of all radii. For this option it is better to use the "Distance transform" method.

4. "Ellipse selection". <br> Use this tool to select ellipse shaped structures. Press and drag the first axis from begin to end. Press and drag the second axis, it will be drawn perpendicular in the middle automatically.

5. "Polyhedron selection". <br> Use this tool to select polyhedron shaped structures. Create edges by press and drag from one vertex to other. When you when you bring the end to an already existing vertex, it is automatically connected. <br> When you are done click "Finish" botton on the top. Select bounding figure and draw it. Parameters of drawn bounding figure will be used in table. 

6. "Amorphous selection". <br> Use this tool to select amorphous structures. Use cursor to draw a bounder by hand. Than select bounding figure or choose option to use area of hand-drawn figure. 

7. "Select unit line". <br> Use this tool to select unit line. Press and drag to drow line above unit line. Than enter its length and scale (you can type in whatever you want).

# Automatic marking

* "Distance Transform" is used to detect touching and overlapping circles in flat pictures. Algorithm uses [distanceTransform OpenCV method](https://docs.opencv.org/4.x/d2/dbd/tutorial_distance_transform.html). More explanation is available in [this question](https://stackoverflow.com/questions/26932891/detect-touching-overlapping-circles-ellipses-with-opencv-and-python).

* "Filter2d" is used for non-flat (spherical) structures in noisy pictures with shadows. It uses [FIlter2D OpenCV method](https://docs.opencv.org/3.4/d4/dbd/tutorial_filter_2d.html) to convert image and match it with sample. Note: you might try use other kernel matrix and circle sample radius to apply it in your scenes. More explanation is available in [this question](https://stackoverflow.com/questions/71903330/opencv-houghcircles-parameters-for-detecting-circles-microstructure-spheres).

* "HoughCircles" is used with simple scenes. It uses [HoughCircle OpenCV transform](https://docs.opencv.org/3.4/d4/d70/tutorial_hough_circle.html). 

# Histogram
Histogram is creating with [seaborn.displot](https://seaborn.pydata.org/generated/seaborn.displot.html)

Data that is used for it is presented in the Table. 

You can export histogram in *.png *.bmp *.jpg *.jpeg fromats.


# Creating .exe / .app files
Use [PyInstaller](https://pyinstaller.org/en/stable/) to create an executable from Python project. Example [manual](https://api.arcade.academy/en/latest/tutorials/bundling_with_pyinstaller/index.html).


**Notes**

I've faced false-trojan warnings on Windows system. I managed to solve it with [this answer](https://stackoverflow.com/a/52054580/17790933) and [this step-by-step manual](https://python.plainenglish.io/pyinstaller-exe-false-positive-trojan-virus-resolved-b33842bd3184). Also, make sure that you have all Python [dependencies](https://wiki.python.org/moin/WindowsCompilers) installed. 

On MacOS make sure you [disabled GateKeeper](https://osxdaily.com/2015/05/04/disable-gatekeeper-command-line-mac-osx/) to allow programms from unverified developers to run created application.

# Licence and Registration
Program is registered with the Federal Service
on Intellectual Property
[Registration form RU 2022663303](https://new.fips.ru/registers-doc-view/fips_servlet?DB=EVM&DocNumber=2022663303&TypeFile=html)
