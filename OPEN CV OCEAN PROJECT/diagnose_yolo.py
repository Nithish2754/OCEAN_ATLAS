from __future__ import annotations

from pathlib import Path

import cv2
from ultralytics import YOLO

from src.oceanatlas.preprocessing import preprocess_frame

MODEL_PATH = Path("runs/detect/runs/detect-3/weights/best.pt")
TEST_IMAGES = {
    "polymetallic_ok": Path("dataset/polymetallic_nodules/deep-sea-mining-climate-3.jpg"),
    "cobalt_ok": Path("dataset/cobalt_rich_crust/images (3).jpg"),
    "hydrothermal_fail": Path("dataset/hydrothermal_sulphides/images (3).jpg"),
}
CONFIDENCE_LEVELS = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]


def describe_image(path: Path) -> list[dict]:
    image = cv2.imread(str(path))
    if image is None:
        raise FileNotFoundError(f"Unable to read image: {path}")
    model = YOLO(str(MODEL_PATH))
    results = model(image, conf=0.05, imgsz=640, verbose=False)
    preds: list[dict] = []
    for result in results:
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            continue
        for box in boxes:
            cls_id = int(box.cls.item())
            conf = float(box.conf.item())
            xyxy = [float(v) for v in box.xyxy[0].tolist()]
            preds.append({
                "class_id": cls_id,
                "confidence": conf,
                "bbox": xyxy,
            })
    return sorted(preds, key=lambda item: item["confidence"], reverse=True)


def show_thresholds(path: Path) -> None:
    image = cv2.imread(str(path))
    if image is None:
        raise FileNotFoundError(f"Unable to read image: {path}")
    model = YOLO(str(MODEL_PATH))
    print(f"\nIMAGE: {path}")
    print("CONFIDENCE SWEEP")
    for threshold in CONFIDENCE_LEVELS:
        results = model(image, conf=threshold, imgsz=640, verbose=False)
        detections = []
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            for box in boxes:
                detections.append({
                    "class_id": int(box.cls.item()),
                    "confidence": float(box.conf.item()),
                    "bbox": [float(v) for v in box.xyxy[0].tolist()],
                })
        accepted = sorted(detections, key=lambda item: item["confidence"], reverse=True)
        if accepted:
            top = accepted[0]
            print(f"  conf>= {threshold:.2f}: class={top['class_id']} confidence={top['confidence']:.4f}")
        else:
            print(f"  conf>= {threshold:.2f}: rejected")


def compare_preprocessing(path: Path) -> None:
    image = cv2.imread(str(path))
    if image is None:
        raise FileNotFoundError(f"Unable to read image: {path}")
    model = YOLO(str(MODEL_PATH))
    print(f"\nIMAGE: {path}")
    print("RAW IMAGE PREDICTIONS")
    raw_results = model(image, conf=0.05, imgsz=640, verbose=False)
    for result in raw_results:
        boxes = getattr(result, "boxes", None)
        if boxes is None or len(boxes) == 0:
            print("  NO PREDICTIONS")
        else:
            for box in boxes:
                cls = int(box.cls.item())
                conf = float(box.conf.item())
                print(f"  class={cls} confidence={conf:.4f} bbox={box.xyxy[0].tolist()}")

    print("PREPROCESSED IMAGE PREDICTIONS")
    processed = preprocess_frame(image, resize_shape=(640, 640))
    proc_results = model(processed, conf=0.05, imgsz=640, verbose=False)
    for result in proc_results:
        boxes = getattr(result, "boxes", None)
        if boxes is None or len(boxes) == 0:
            print("  NO PREDICTIONS")
        else:
            for box in boxes:
                cls = int(box.cls.item())
                conf = float(box.conf.item())
                print(f"  class={cls} confidence={conf:.4f} bbox={box.xyxy[0].tolist()}")


def main() -> None:
    model = YOLO(str(MODEL_PATH))
    print("MODEL PATH:", MODEL_PATH)
    print("MODEL CLASSES:", model.names)

    for name, path in TEST_IMAGES.items():
        print(f"\n=== {name.upper()} ===")
        raw = describe_image(path)
        if not raw:
            print("RAW PREDICTIONS: NO DETECTIONS")
        else:
            print("RAW PREDICTIONS:")
            for item in raw:
                print(f"  class={item['class_id']} confidence={item['confidence']:.4f} bbox={item['bbox']}")

        accepted = [x for x in raw if x["confidence"] >= 0.25]
        if accepted:
            print("AFTER CONFIDENCE FILTER @0.25:")
            for item in accepted:
                print(f"  class={item['class_id']} confidence={item['confidence']:.4f} bbox={item['bbox']}")
        else:
            print("AFTER CONFIDENCE FILTER @0.25: NO ACCEPTED DETECTIONS")

        show_thresholds(path)
        compare_preprocessing(path)


if __name__ == "__main__":
    main()
