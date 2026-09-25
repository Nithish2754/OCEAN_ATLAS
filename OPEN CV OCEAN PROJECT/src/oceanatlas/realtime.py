from __future__ import annotations

from collections import Counter
from typing import Optional

import cv2
import numpy as np


def detect_sample_presence(frame: np.ndarray, min_area: int = 5000):
    """Return (is_empty, bounding_box) using background subtraction and contour area checks."""
    if frame is None or frame.size == 0:
        raise ValueError("Frame is empty.")

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 30, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return True, None

    max_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(max_contour)
    if area < min_area:
        return True, None

    x, y, w, h = cv2.boundingRect(max_contour)
    return False, (x, y, w, h)


def majority_vote_label(labels: list[str]) -> str:
    if not labels:
        return "Awaiting sample..."
    counts = Counter(labels)
    return counts.most_common(1)[0][0]


def build_sample_region(frame: np.ndarray, box: Optional[tuple[int, int, int, int]]):
    if box is None:
        return frame.copy()
    x, y, w, h = box
    x = max(0, x)
    y = max(0, y)
    w = max(1, w)
    h = max(1, h)
    return frame[y : y + h, x : x + w]
