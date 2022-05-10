import cv2
import numpy as np
import tkinter.messagebox as mb


def nms_indices(boxes, overlap_thresh=0.4):
    if len(boxes) == 0:
        return []
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
        if np.any(overlap) > overlap_thresh:
            indices = indices[indices != i]
    return indices


def nms(og_borders, stretch_factor=2):
    # og_boundings = list of (x, y, w, h) - rectangle boxes
    # returns filtered list
    borders = list()
    for x, y, w, h in og_borders:
        borders.append((x - w * (stretch_factor - 1) / 2,
                        y - h * (stretch_factor - 1) / 2,
                        x + w * (1 + (stretch_factor - 1) / 2),
                        y + h * (1 + (stretch_factor - 1) / 2)))
    borders = np.array(borders).astype(int)
    og_borders = np.array(og_borders)[nms_indices(borders)].astype(int)
    return og_borders


def find_circles_with_radius_distance(path, radius=0, original_center=None):
    im = cv2.imread(path)

    if im is None:
        mb.showwarning("Warning", "Original image was removed")
        return

    # im = cv2.GaussianBlur(im, (3, 3), 0)
    # im = cv2.medianBlur(im, 7)
    # im = cv2.blur(im, (3, 3))

    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    th, bw = cv2.threshold(hsv[:, :, 2], 0, 255,
                           cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    laplacian_filtered = cv2.Laplacian(bw, cv2.CV_8UC1)
    if (cv2.Laplacian(bw, cv2.CV_8UC1).var() - cv2.Laplacian(
            bw - laplacian_filtered, cv2.CV_8UC1).var() > 45):
        bw = bw - cv2.Laplacian(bw, cv2.CV_8UC1)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    morph = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel)
    dist = cv2.distanceTransform(morph, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    borderSize = int(radius * 1.1) if radius != 0 else 30
    distborder = cv2.copyMakeBorder(dist, borderSize, borderSize,
                                    borderSize, borderSize,
                                    cv2.BORDER_CONSTANT | cv2.BORDER_ISOLATED,
                                    0)
    gap = int(radius * 0.9) if radius != 0 else 10
    kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (
        2 * (borderSize - gap) + 1, 2 * (borderSize - gap) + 1))
    kernel2 = cv2.copyMakeBorder(kernel2, gap, gap, gap, gap,
                                 cv2.BORDER_CONSTANT | cv2.BORDER_ISOLATED,
                                 0)
    distTempl = cv2.distanceTransform(kernel2, cv2.DIST_L2,
                                      cv2.DIST_MASK_PRECISE)
    nxcor = cv2.matchTemplate(distborder, distTempl, cv2.TM_CCOEFF_NORMED)
    mn, mx, _, _ = cv2.minMaxLoc(nxcor)
    th, peaks = cv2.threshold(nxcor, mx * 0.5, 255, cv2.THRESH_BINARY)
    peaks8u = cv2.convertScaleAbs(peaks)
    contours, hierarchy = cv2.findContours(peaks8u, cv2.RETR_CCOMP,
                                           cv2.CHAIN_APPROX_SIMPLE)
    peaks8u = cv2.convertScaleAbs(peaks)

    circles = list()
    borders = list()
    for i in range(len(contours)):
        x, y, w, h = cv2.boundingRect(contours[i])
        borders.append((x, y, w, h))

    if radius != 0:
        borders.append((*original_center, radius, radius))
        nms(borders)

    for x, y, w, h in nms(borders):
        _, mx, _, mxloc = cv2.minMaxLoc(dist[y:y + h, x:x + w],
                                        peaks8u[y:y + h, x:x + w])
        circle_radius = mx

        if not (0.85 * radius <= circle_radius <= 1.15 * radius) \
                and radius != 0:
            continue

        if radius == 0 and circle_radius <= 12:
            continue

        circles.append((mxloc[0] + x, mxloc[1] + y, circle_radius))

    return circles


def find_circles_with_radius_filter2d(path, radius=0, original_center=None):
    img = cv2.imread(path)

    if img is None:
        mb.showwarning("Warning", "Original image was removed")
        return

    resize_scale = 0.5

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (0, 0), gray, resize_scale, resize_scale,
                      cv2.INTER_AREA)

    radius = round(radius * resize_scale)

    test = cv2.medianBlur(gray, 5)
    # struct_elem = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    # might be better to use "I" matrix
    struct_elem = np.ones((5, 5), np.uint8)

    test = cv2.morphologyEx(test, cv2.MORPH_GRADIENT, kernel=struct_elem)

    edge_img = cv2.adaptiveThreshold(test, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY,
                                     int(len(test) / 6) | 0x01, -6)

    filter_radius = radius + 2
    filter_size = filter_radius * 2 + 1
    img_filter = np.zeros((filter_size, filter_size))

    cv2.circle(img_filter, (filter_radius, filter_radius), int(radius / 2), -1,
               -1)
    cv2.circle(img_filter, (filter_radius, filter_radius), radius, 1, 6)
    # second circle better to generate with smaller width like this:
    # cv2.circle(img_filter, (filter_radius, filter_radius), radius, 1, 3)

    filter_result = cv2.filter2D(edge_img, cv2.CV_32F, img_filter)

    min_val, max_val, _, _ = cv2.minMaxLoc(filter_result)
    scale = 255 / (max_val - min_val)
    show = np.uint8(filter_result * scale - min_val * scale)

    _, peaks = cv2.threshold(filter_result, (max_val + min_val) * 0.6, 255,
                             cv2.THRESH_BINARY)
    peaks8u = np.uint8(peaks)
    show = gray.copy()

    show[np.where(peaks8u == 255)] = 255

    _, peaks = cv2.threshold(filter_result, (max_val + min_val) * 0.6, 255,
                             cv2.THRESH_BINARY)
    peaks8u = np.uint8(peaks)
    show = gray.copy() * 0.5

    show[np.where(peaks8u == 255)] = 255

    contours, hierarchy = cv2.findContours(peaks8u, cv2.RETR_CCOMP,
                                           cv2.CHAIN_APPROX_SIMPLE)
    peaks8u = cv2.convertScaleAbs(peaks)  # to use as mask
    circles = list()
    borders = list()

    for i in range(len(contours)):
        x, y, w, h = cv2.boundingRect(contours[i])
        borders.append((x, y, w, h))

    if radius != 0:
        borders.append((*original_center, radius, radius))
        nms(borders)

    for x, y, w, h in nms(borders):
        _, _, _, maxloc = cv2.minMaxLoc(filter_result[y:y + h, x:x + w],
                                        peaks8u[y:y + h, x:x + w])

        x, y, w, h = int(x / resize_scale), int(y / resize_scale), int(
            w / resize_scale), int(h / resize_scale)
        maxloc_x, maxloc_y = maxloc
        maxloc_x, maxloc_y = int(maxloc_x / resize_scale), int(
            maxloc_y / resize_scale)
        maxloc = (maxloc_x, maxloc_y)

        circles.append((maxloc[0] + x, maxloc[0] + y, radius / resize_scale))

    return circles


def find_circles_with_radius_hough(path, radius=0, original_center=None):
    img = cv2.imread(path)
    if img is None:
        mb.showwarning("Warning", "Original image was removed")
        return

    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_gray = cv2.medianBlur(img_gray, 5)

    circles = None
    if radius != 0:
        circles = cv2.HoughCircles(img_gray, cv2.HOUGH_GRADIENT, 2,
                                   radius * 1.75,
                                   param1=50, param2=30,
                                   minRadius=int(radius * 0.9),
                                   maxRadius=int(radius * 1.1))
    else:
        circles = cv2.HoughCircles(img_gray, cv2.HOUGH_GRADIENT, 2,
                                   50, param1=100, param2=50, minRadius=10)
        # 120 30
        # 120 35
        # 120 40
        # 130 32
        # 130 35 - cool
    if circles is None:
        return list()

    res = list()
    borders = list()

    for i in circles[0, :]:
        borders.append((i[0] - i[2] / 2, i[1] - i[2] / 2, i[2], i[2]))

    if len(circles[0, :]) > 100 and radius == 0:
        return list()

    if radius != 0:
        x, y = original_center
        borders.append((x - radius / 2, y - radius / 2, radius, radius))

    # borders = nms(borders, 1)

    for x, y, r1, r2 in borders:
        res.append((x + r1 / 2, y + r1 / 2, r1))

    return res
