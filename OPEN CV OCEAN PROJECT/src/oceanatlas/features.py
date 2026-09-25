from __future__ import annotations

import cv2
import numpy as np
from skimage.feature import local_binary_pattern

from .preprocessing import preprocess_frame


def _hsv_histogram(frame: np.ndarray, bins: tuple[int, int, int] = (8, 8, 8)) -> np.ndarray:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist(
        [hsv],
        channels=[0, 1, 2],
        mask=None,
        histSize=list(bins),
        ranges=[0, 180, 0, 256, 0, 256],
    )
    hist = hist.flatten().astype(np.float32)
    if hist.sum() > 0:
        hist /= hist.sum()
    return hist


def _gray_level_cooccurrence_like_features(gray: np.ndarray) -> np.ndarray:
    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = cv2.magnitude(grad_x, grad_y)
    mean_mag = float(np.mean(magnitude))
    std_mag = float(np.std(magnitude))
    entropy = float(-np.sum((np.histogram(gray, 32)[0] / max(gray.size, 1)) * np.log2(np.histogram(gray, 32)[0] / max(gray.size, 1) + 1e-6)))
    return np.array([mean_mag, std_mag, entropy], dtype=np.float32)


def _contour_shape_features(gray: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return np.array([0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)

    areas = []
    roundness = []
    perimeters = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 30:
            continue
        perimeter = cv2.arcLength(contour, True)
        if perimeter > 0:
            circularity = 4.0 * np.pi * area / (perimeter * perimeter)
            roundness.append(float(circularity))
        areas.append(float(area))
        perimeters.append(float(perimeter))

    if not areas:
        return np.array([0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)

    mean_area = float(np.mean(areas))
    total_area = float(np.sum(areas))
    mean_round = float(np.mean(roundness)) if roundness else 0.0
    contour_count = float(len(areas))
    mean_perimeter = float(np.mean(perimeters)) if perimeters else 0.0
    edge_density = float(np.mean(cv2.Canny(gray, 50, 150)) / 255.0)
    return np.array([mean_area, total_area, mean_round, contour_count, mean_perimeter, edge_density], dtype=np.float32)


def _lbp_histogram(gray: np.ndarray, bins: int = 59) -> np.ndarray:
    lbp = local_binary_pattern(gray, 8, 1, method="uniform")
    hist, _ = np.histogram(lbp.ravel(), bins=bins, range=(0, bins))
    hist = hist.astype(np.float32)
    if hist.sum() > 0:
        hist /= hist.sum()
    return hist


def extract_frame_features(frame: np.ndarray, resize_shape: tuple[int, int] = (224, 224)) -> np.ndarray:
    """Build one feature vector from a single underwater camera frame."""
    processed = preprocess_frame(frame, resize_shape=resize_shape)
    gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)

    hsv = _hsv_histogram(processed)
    lbp = _lbp_histogram(gray)
    texture = _gray_level_cooccurrence_like_features(gray)
    contour = _contour_shape_features(gray)

    edge_map = cv2.Canny(gray, 50, 150)
    edge_density = float(np.mean(edge_map) / 255.0)
    luminance_std = float(np.std(gray))

    feature_vector = np.concatenate([
        hsv,
        lbp,
        texture,
        contour,
        np.array([edge_density, luminance_std], dtype=np.float32),
    ])
    return feature_vector.astype(np.float32)


def build_visual_payload(visual_class: str, confidence: float) -> dict:
    """Return a JSON-friendly payload describing the visual detection outcome."""
    base = {
        "visual_class": visual_class,
        "confidence": float(confidence),
    }

    if visual_class == "polymetallic_nodules":
        base["message"] = "Polymetallic nodules detected with a bounded nodule-like visual pattern."
    elif visual_class == "hydrothermal_sulphide":
        base["message"] = "Hydrothermal sulphide detected with a chimney-like or vent-like structure."
    elif visual_class == "cobalt_rich_crust":
        base["message"] = "Cobalt-rich crust detected with a dense pavement-like crust texture."
    else:
        base["message"] = "Visual class was not recognized."

    return base
