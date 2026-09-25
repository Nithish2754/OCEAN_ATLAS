from __future__ import annotations

import argparse
import json

import cv2
import numpy as np

from .features import build_visual_payload
from .yolo_pipeline import TemporalDetectionSmoother, YOLODetector, build_detection_payload


def _safe_imshow(window_name: str, frame: np.ndarray) -> bool:
    try:
        cv2.imshow(window_name, frame)
        return True
    except cv2.error:
        return False


def _safe_wait_key(delay_ms: int) -> int:
    try:
        return cv2.waitKey(delay_ms)
    except cv2.error:
        return -1


def _detect_faces(frame: np.ndarray) -> list[tuple[int, int, int, int]]:
    if not hasattr(cv2, "CascadeClassifier") or not hasattr(cv2, "data"):
        return []
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return [tuple(int(value) for value in face) for face in cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))]


def _boxes_overlap(left: list[int], right: tuple[int, int, int, int]) -> bool:
    left_x1, left_y1, left_width, left_height = left
    right_x1, right_y1, right_width, right_height = right
    left_x2, left_y2 = left_x1 + left_width, left_y1 + left_height
    right_x2, right_y2 = right_x1 + right_width, right_y1 + right_height
    return max(left_x1, right_x1) < min(left_x2, right_x2) and max(left_y1, right_y1) < min(left_y2, right_y2)


def _is_oversized_box(item: dict, frame_shape: tuple[int, int, int], max_area_ratio: float = 0.92) -> bool:
    frame_height, frame_width = frame_shape[:2]
    _, _, box_width, box_height = item["bbox"]
    frame_area = max(frame_width * frame_height, 1)
    return (box_width * box_height) / frame_area > max_area_ratio


def run_live_pipeline(
    camera_index: int = 0,
    model_path: str | None = None,
    dataset_dir: str | None = None,
    vote_window: int = 10,
    confidence: float = 0.25,
    stable_frames: int = 3,
    iou_threshold: float = 0.4,
    underwater_preprocess: bool = False,
    max_box_area_ratio: float = 0.92,
):
    del dataset_dir, vote_window
    model = model_path or "runs/detect/runs/detect-3/weights/best.pt"
    detector = YOLODetector(
        model_path=model,
        conf_threshold=confidence,
        preprocess_input=underwater_preprocess,
    )
    smoother = TemporalDetectionSmoother(stable_frames=stable_frames, iou_threshold=iou_threshold)

    video = cv2.VideoCapture(camera_index)
    if not video.isOpened():
        raise RuntimeError(f"Unable to open camera index {camera_index}.")

    while True:
        success, frame = video.read()
        if not success or frame is None:
            break

        display = frame.copy()
        results = detector.detect(frame, conf_threshold=confidence)
        detections = detector.parse_results(results, frame.shape)
        detections = [item for item in detections if not _is_oversized_box(item, frame.shape, max_box_area_ratio)]
        detections = smoother.update(detections)
        faces = _detect_faces(frame) if detections else []
        detections = [item for item in detections if not any(_boxes_overlap(item["bbox"], face) for face in faces)]

        if detections:
            for item in detections:
                label = item["class"]
                detection_confidence = float(item["confidence"])
                x1, y1, w, h = item["bbox"]
                x2 = x1 + w
                y2 = y1 + h
                color = {
                    "polymetallic_nodules": (0, 255, 255),
                    "cobalt_rich_crust": (255, 0, 255),
                    "hydrothermal_sulphide": (0, 255, 0),
                }.get(label, (255, 255, 255))
                cv2.rectangle(display, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                cv2.putText(
                    display,
                    f"{label}: {detection_confidence:.2f}",
                    (int(x1), max(20, int(y1) - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2,
                    cv2.LINE_AA,
                )

            payload = build_detection_payload(
                device_id="ROV-3-CAM",
                detections=[
                    {
                        "class": item["class"],
                        "confidence": float(item["confidence"]),
                        "bbox": item["bbox"],
                    }
                    for item in detections
                ],
            )
            print(json.dumps(payload))
        else:
            cv2.putText(
                display,
                "No deposit detected",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )

        _safe_imshow("OceanAtlas YOLO detector", display)
        if _safe_wait_key(1) & 0xFF == ord("q"):
            break

    video.release()
    try:
        cv2.destroyAllWindows()
    except cv2.error:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OceanAtlas YOLO real-time underwater deposit detector")
    parser.add_argument("--camera-index", type=int, default=0, help="OpenCV video capture index")
    parser.add_argument("--model-path", type=str, default=None, help="Path to a trained YOLO model (.pt)")
    parser.add_argument("--confidence", type=float, default=0.25, help="Minimum detection confidence")
    parser.add_argument("--stable-frames", type=int, default=3, help="Consecutive matching frames required")
    parser.add_argument("--iou-threshold", type=float, default=0.4, help="Minimum box IoU for temporal agreement")
    parser.add_argument("--underwater-preprocess", action="store_true", help="Apply color correction/CLAHE/denoising before YOLO")
    parser.add_argument("--max-box-area-ratio", type=float, default=0.92, help="Reject boxes covering more than this fraction of the frame")
    parser.add_argument("--dataset-dir", type=str, default=None, help="Deprecated compatibility argument; YOLO uses annotated datasets")
    parser.add_argument("--vote-window", type=int, default=10, help="Compatibility argument retained for older pipelines")
    args = parser.parse_args()
    run_live_pipeline(
        args.camera_index,
        args.model_path,
        args.dataset_dir,
        args.vote_window,
        args.confidence,
        args.stable_frames,
        args.iou_threshold,
        args.underwater_preprocess,
        args.max_box_area_ratio,
    )
