from __future__ import annotations

import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:  # opencv в optional-группе "detection"
    cv2 = None
    CV2_AVAILABLE = False

INSTALL_HINT = ('Automatic detection requires OpenCV. Install it with:\n'
                '    uv sync --extra detection')


class DetectionUnavailableError(Exception):
    """OpenCV is not installed (the "detection" extra)."""


def _require_cv2() -> None:
    if not CV2_AVAILABLE:
        raise DetectionUnavailableError(INSTALL_HINT)


class ImageReadError(Exception):
    """Исходное изображение недоступно."""


def _read(path: str) -> np.ndarray:
    image = cv2.imread(path)
    if image is None:
        raise ImageReadError(f"Cannot read image: {path}")
    return image


def nms_indices(boxes: np.ndarray, overlap_thresh: float = 0.4) -> np.ndarray:
    if len(boxes) == 0:
        return np.array([], dtype=int)
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    indices = np.arange(len(x1))
    for i, box in enumerate(boxes):
        temp_indices = indices[indices != i]
        xx1 = np.maximum(box[0], boxes[temp_indices, 0])
        yy1 = np.maximum(box[1], boxes[temp_indices, 1])
        xx2 = np.minimum(box[2], boxes[temp_indices, 2])
        yy2 = np.minimum(box[3], boxes[temp_indices, 3])
        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)

        overlap = (w * h) / areas[temp_indices]
        if np.any(overlap > overlap_thresh):
            indices = indices[indices != i]
    return indices


def nms(og_borders: list, stretch_factor: float = 2) -> np.ndarray:
    """Не-максимальное подавление для списка прямоугольников (x, y, w, h)."""
    borders = [
        (x - w * (stretch_factor - 1) / 2,
         y - h * (stretch_factor - 1) / 2,
         x + w * (1 + (stretch_factor - 1) / 2),
         y + h * (1 + (stretch_factor - 1) / 2))
        for x, y, w, h in og_borders
    ]
    borders = np.array(borders).astype(int)
    return np.array(og_borders)[nms_indices(borders)].astype(int)


def _distance_pipeline(im: np.ndarray, radius: float):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    _, bw = cv2.threshold(hsv[:, :, 2], 0, 255,
                          cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    laplacian_filtered = cv2.Laplacian(bw, cv2.CV_8UC1)
    if (cv2.Laplacian(bw, cv2.CV_8UC1).var()
            - cv2.Laplacian(bw - laplacian_filtered, cv2.CV_8UC1).var() > 45):
        bw = bw - cv2.Laplacian(bw, cv2.CV_8UC1)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    morph = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel)
    dist = cv2.distanceTransform(morph, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    border_size = int(radius * 1.1) if radius else 30
    distborder = cv2.copyMakeBorder(dist, border_size, border_size,
                                    border_size, border_size,
                                    cv2.BORDER_CONSTANT
                                    | cv2.BORDER_ISOLATED, 0)
    gap = int(radius * 0.9) if radius else 10
    kernel2 = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2 * (border_size - gap) + 1,
                            2 * (border_size - gap) + 1))
    kernel2 = cv2.copyMakeBorder(kernel2, gap, gap, gap, gap,
                                 cv2.BORDER_CONSTANT
                                 | cv2.BORDER_ISOLATED, 0)
    dist_templ = cv2.distanceTransform(kernel2, cv2.DIST_L2,
                                       cv2.DIST_MASK_PRECISE)
    nxcor = cv2.matchTemplate(distborder, dist_templ, cv2.TM_CCOEFF_NORMED)
    _, mx, _, _ = cv2.minMaxLoc(nxcor)
    _, peaks = cv2.threshold(nxcor, mx * 0.5, 255, cv2.THRESH_BINARY)
    peaks8u = cv2.convertScaleAbs(peaks)
    contours, _ = cv2.findContours(peaks8u, cv2.RETR_CCOMP,
                                   cv2.CHAIN_APPROX_SIMPLE)
    return dist, peaks8u, contours


def find_circles_distance(path: str, radius: float = 0,
                          original_center: tuple | None = None) -> list[tuple]:
    """Детекция окружностей через distance transform.

    radius == 0 — искать окружности всех радиусов, иначе — только
    с радиусом ±15% от заданного вокруг original_center.
    """
    _require_cv2()
    im = _read(path)
    dist, peaks8u, contours = _distance_pipeline(im, radius)

    borders = [cv2.boundingRect(c) for c in contours]
    if radius:
        borders.append((*original_center, radius, radius))

    circles = []
    for x, y, w, h in nms(borders):
        _, mx, _, mxloc = cv2.minMaxLoc(dist[y:y + h, x:x + w],
                                        peaks8u[y:y + h, x:x + w])
        circle_radius = mx

        if radius and not (0.85 * radius <= circle_radius <= 1.15 * radius):
            continue
        if not radius and circle_radius <= 12:
            continue

        circles.append((mxloc[0] + x, mxloc[1] + y, circle_radius))
    return circles


def find_circles_filter2d(path: str, radius: float = 0,
                          original_center: tuple | None = None) -> list[tuple]:
    """Детекция неплоских (сферических) структур через Filter2D.
    Подходит для шумных снимков с тенями."""
    _require_cv2()
    img = _read(path)
    resize_scale = 0.5

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (0, 0), gray, resize_scale, resize_scale,
                      cv2.INTER_AREA)
    radius = round(radius * resize_scale)

    test = cv2.medianBlur(gray, 5)
    struct_elem = np.ones((5, 5), np.uint8)
    test = cv2.morphologyEx(test, cv2.MORPH_GRADIENT, kernel=struct_elem)
    edge_img = cv2.adaptiveThreshold(test, 255,
                                     cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY,
                                     int(len(test) / 6) | 0x01, -6)

    filter_radius = radius + 2
    filter_size = filter_radius * 2 + 1
    img_filter = np.zeros((filter_size, filter_size))
    cv2.circle(img_filter, (filter_radius, filter_radius),
               max(int(radius / 2), 1), -1, -1)
    cv2.circle(img_filter, (filter_radius, filter_radius), radius, 1, 6)

    filter_result = cv2.filter2D(edge_img, cv2.CV_32F, img_filter)
    min_val, max_val, _, _ = cv2.minMaxLoc(filter_result)

    _, peaks = cv2.threshold(filter_result, (max_val + min_val) * 0.6,
                             255, cv2.THRESH_BINARY)
    peaks8u = np.uint8(peaks)

    contours, _ = cv2.findContours(peaks8u, cv2.RETR_CCOMP,
                                   cv2.CHAIN_APPROX_SIMPLE)
    peaks8u = cv2.convertScaleAbs(peaks)  # маска

    borders = [cv2.boundingRect(c) for c in contours]
    if radius:
        borders.append((*original_center, radius, radius))

    circles = []
    for x, y, w, h in nms(borders):
        _, _, _, maxloc = cv2.minMaxLoc(filter_result[y:y + h, x:x + w],
                                        peaks8u[y:y + h, x:x + w])
        circles.append(((maxloc[0] + x) / resize_scale,
                        (maxloc[1] + y) / resize_scale,
                        radius / resize_scale))
    return circles


def find_circles_hough(path: str, radius: float = 0,
                       original_center: tuple | None = None) -> list[tuple]:
    """Детекция окружностей через преобразование Хафа. Для простых сцен."""
    _require_cv2()
    img = _read(path)
    resize_scale = 0.5

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (0, 0), gray, resize_scale, resize_scale,
                      cv2.INTER_AREA)
    gray = cv2.medianBlur(gray, 5)

    if radius:
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 2,
                                   radius * resize_scale * 1.75,
                                   param1=50, param2=30,
                                   minRadius=int(radius * resize_scale * 0.9),
                                   maxRadius=int(radius * resize_scale * 1.1))
    else:
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT_ALT, 1.5,
                                   20, param1=1, param2=0.4,
                                   minRadius=10, maxRadius=30)
    if circles is None or (len(circles[0, :]) > 100 and not radius):
        return []

    borders = [(i[0] - i[2] / 2, i[1] - i[2] / 2, i[2], i[2])
               for i in circles[0, :]]
    if radius:
        x, y = original_center
        borders.append(((x - radius / 2) * resize_scale,
                        (y - radius / 2) * resize_scale,
                        radius * resize_scale, radius * resize_scale))

    result = []
    for x, y, w, _ in nms(borders, 1):
        result.append(((x + w / 2) / resize_scale,
                       (y + w / 2) / resize_scale,
                       w / resize_scale))
    return result
