"""Automatic circle detection backed by OpenCV.

OpenCV (and its heavy companion packages) is an *optional* dependency. If it is
not installed, the UI shows a warning and detection is disabled rather than
crashing -- this keeps the base install small and fast.
"""

from __future__ import annotations

try:  # pragma: no cover - depends on the environment
    import cv2
    import numpy as np

    _CV2_AVAILABLE = True
except ImportError:  # pragma: no cover
    cv2 = None
    np = None
    _CV2_AVAILABLE = False


def is_available() -> bool:
    """Return ``True`` when the OpenCV-backed backend can be used."""
    return _CV2_AVAILABLE


def missing_message() -> str:
    """Human-readable hint shown when OpenCV is required but absent."""
    return (
        "Automatic detection requires the optional vision dependencies.\n\n"
        "Install them with:\n"
        "    uv run --extra vision structure-editor\n"
        "or\n"
        "    uv sync --extra vision"
    )


def _require_cv2():
    if not _CV2_AVAILABLE:
        raise RuntimeError(missing_message())


def _nms_indices(boxes, indices, overlap_thresh=0.4):
    """Greedy non-maximum suppression over the given array of boxes."""
    boxes = np.asarray(boxes, dtype=float)
    if len(boxes) == 0:
        return []
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    keep = list(indices)
    for i in list(keep):
        rest = [j for j in keep if j != i]
        if not rest:
            break
        xx1 = np.maximum(x1[i], x1[rest])
        yy1 = np.maximum(y1[i], y1[rest])
        xx2 = np.minimum(x2[i], x2[rest])
        yy2 = np.minimum(y2[i], y2[rest])
        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)
        overlap = (w * h) / areas[rest]
        if np.any(overlap > overlap_thresh):
            keep = [j for j in keep if j != i]
    return keep


def find_circles_distance_transform(path, radius=0.0, original_center=None):
    """Detect circles in a flat image using the distance-transform method.

    Returns a list of ``(x, y, radius)`` tuples in image coordinates.
    """
    _require_cv2()

    im = cv2.imread(path)
    if im is None:
        raise FileNotFoundError(f"Could not read image at {path!r}")

    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    _, bw = cv2.threshold(hsv[:, :, 2], 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    laplacian = cv2.Laplacian(bw, cv2.CV_8UC1)
    if cv2.Laplacian(bw, cv2.CV_8UC1).var() - cv2.Laplacian(bw - laplacian, cv2.CV_8UC1).var() > 45:
        bw = bw - laplacian

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    morph = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel)
    dist = cv2.distanceTransform(morph, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)

    border = int(radius * 1.1) if radius else 30
    distborder = cv2.copyMakeBorder(
        dist, border, border, border, border, cv2.BORDER_CONSTANT | cv2.BORDER_ISOLATED, 0
    )
    gap = int(radius * 0.9) if radius else 10
    kernel2 = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2 * (border - gap) + 1, 2 * (border - gap) + 1)
    )
    kernel2 = cv2.copyMakeBorder(
        kernel2, gap, gap, gap, gap, cv2.BORDER_CONSTANT | cv2.BORDER_ISOLATED, 0
    )
    distTempl = cv2.distanceTransform(kernel2, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    nxcor = cv2.matchTemplate(distborder, distTempl, cv2.TM_CCOEFF_NORMED)
    _, mx, _, _ = cv2.minMaxLoc(nxcor)
    _, peaks = cv2.threshold(nxcor, mx * 0.5, 255, cv2.THRESH_BINARY)
    peaks8u = cv2.convertScaleAbs(peaks)
    contours, _ = cv2.findContours(peaks8u, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    peaks8u = cv2.convertScaleAbs(peaks)

    borders = [cv2.boundingRect(c) for c in contours]
    if radius != 0 and original_center is not None:
        borders.append((*original_center, radius, radius))

    # Third return of NMS is a filtered index list operating on ``borders``.
    keep = _nms_indices(
        [(bx, by, bx + bw, by + bh) for bx, by, bw, bh in borders], list(range(len(borders)))
    )
    circles: list[tuple[float, float, float]] = []
    for i in keep:
        x, y, w, h = borders[i]
        _, mx, _, mxloc = cv2.minMaxLoc(dist[y : y + h, x : x + w], peaks8u[y : y + h, x : x + w])
        circle_radius = mx
        if radius != 0 and not (0.85 * radius <= circle_radius <= 1.15 * radius):
            continue
        if radius == 0 and circle_radius <= 12:
            continue
        circles.append((mxloc[0] + x, mxloc[1] + y, circle_radius))
    return circles
