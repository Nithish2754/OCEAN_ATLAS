from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from .preprocessing import preprocess_frame

YOLO_CLASS_NAMES = [
    "polymetallic_nodules",
    "cobalt_rich_crust",
    "hydrothermal_sulphide",
]


def _box_iou(left: list[int], right: list[int]) -> float:
    left_x1, left_y1, left_w, left_h = left
    right_x1, right_y1, right_w, right_h = right
    left_x2, left_y2 = left_x1 + left_w, left_y1 + left_h
    right_x2, right_y2 = right_x1 + right_w, right_y1 + right_h
    intersection_x1 = max(left_x1, right_x1)
    intersection_y1 = max(left_y1, right_y1)
    intersection_x2 = min(left_x2, right_x2)
    intersection_y2 = min(left_y2, right_y2)
    intersection = max(0, intersection_x2 - intersection_x1) * max(0, intersection_y2 - intersection_y1)
    union = left_w * left_h + right_w * right_h - intersection
    return intersection / union if union else 0.0


class TemporalDetectionSmoother:
    """Accept a detection only after repeated class and box agreement."""

    def __init__(self, stable_frames: int = 3, iou_threshold: float = 0.4, history_size: int = 5):
        if stable_frames < 1:
            raise ValueError("stable_frames must be positive")
        self.stable_frames = stable_frames
        self.iou_threshold = iou_threshold
        self.history = deque(maxlen=max(stable_frames, history_size))

    def update(self, detections: list[dict]) -> list[dict]:
        current = max(detections, key=lambda item: item["confidence"]) if detections else None
        self.history.append(current)
        if current is None or len(self.history) < self.stable_frames:
            return []
        recent = list(self.history)[-self.stable_frames:]
        if any(item is None for item in recent):
            return []
        first = recent[0]
        if any(
            item["class"] != first["class"] or _box_iou(item["bbox"], first["bbox"]) < self.iou_threshold
            for item in recent[1:]
        ):
            return []
        return [dict(current)]


def build_detection_payload(device_id: str = "ROV-3-CAM", detections: list[dict] | None = None) -> dict:
    payload = {
        "device_id": device_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "detections": detections or [],
    }
    return payload


class YOLODetector:
    def __init__(
        self,
        model_path: str | Path | None = None,
        device: str = "cpu",
        conf_threshold: float = 0.25,
        preprocess_input: bool = False,
    ):
        self.model_path = str(model_path) if model_path is not None else None
        self.device = device
        self.conf_threshold = conf_threshold
        self.preprocess_input = preprocess_input
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO
        except ModuleNotFoundError as exc:  # pragma: no cover - environment guard
            raise RuntimeError(
                "ultralytics is not installed. Install the YOLO dependency to run the detection pipeline."
            ) from exc

        if self.model_path is not None:
            model_file = Path(self.model_path)
            if not model_file.exists() and model_file.name == "best.pt":
                candidates = sorted(
                    Path("runs").glob("**/weights/best.pt"),
                    key=lambda path: path.stat().st_mtime,
                    reverse=True,
                )
                if candidates:
                    model_file = candidates[0]
            if model_file.exists():
                self.model = YOLO(str(model_file))
                return
            raise FileNotFoundError(
                f"YOLO model file not found: {model_file}. "
                "Expected a .pt checkpoint such as runs/detect/runs/detect-3/weights/best.pt."
            )

        self.model = YOLO("yolov8n.pt")

    def detect(self, frame: np.ndarray, conf_threshold: float | None = None):
        if self.model is None:
            raise RuntimeError("YOLO model is not initialized.")

        target_conf = self.conf_threshold if conf_threshold is None else conf_threshold
        processed = preprocess_frame(frame, resize_shape=(640, 640)) if self.preprocess_input else frame
        results = self.model(processed, conf=target_conf, device=self.device, verbose=False)
        return results

    @staticmethod
    def parse_results(results, image_shape: tuple[int, int, int] | None = None):
        parsed = []
        if not results:
            return parsed

        result = results[0]
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            return parsed

        result_height, result_width = result.orig_shape[:2]
        height, width = (image_shape[:2] if image_shape is not None else (result_height, result_width))
        scale_x = width / result_width
        scale_y = height / result_height
        for box in boxes:
            cls_index = int(box.cls.item())
            class_name = YOLO_CLASS_NAMES[cls_index] if cls_index < len(YOLO_CLASS_NAMES) else str(cls_index)
            confidence = float(box.conf.item())
            x1, y1, x2, y2 = map(float, box.xyxy[0].tolist())
            x1 *= scale_x
            x2 *= scale_x
            y1 *= scale_y
            y2 *= scale_y
            bbox = [int(round(x1)), int(round(y1)), int(round(x2 - x1)), int(round(y2 - y1))]
            parsed.append({
                "class": class_name,
                "confidence": confidence,
                "bbox": bbox,
                "image_size": [width, height],
            })
        return parsed

    def detect_and_package(self, frame: np.ndarray, device_id: str = "ROV-3-CAM", conf_threshold: float | None = None):
        results = self.detect(frame, conf_threshold=conf_threshold)
        detections = self.parse_results(results, frame.shape)
        filtered = [
            {
                "class": item["class"],
                "confidence": float(item["confidence"]),
                "bbox": item["bbox"],
            }
            for item in detections
            if item["class"] in YOLO_CLASS_NAMES
        ]
        return build_detection_payload(device_id=device_id, detections=filtered)
