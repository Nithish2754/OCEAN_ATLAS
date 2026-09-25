from __future__ import annotations

import argparse
from pathlib import Path

import cv2
from ultralytics import YOLO

from oceanatlas.preprocessing import preprocess_frame


def inspect(model: YOLO, image_path: Path, confidence: float, iou: float, preprocess: bool) -> None:
    frame = cv2.imread(str(image_path))
    if frame is None:
        raise RuntimeError(f"Unable to read image: {image_path}")
    input_frame = preprocess_frame(frame, (640, 640)) if preprocess else frame
    results = model(input_frame, conf=0.001, iou=iou, verbose=False)
    result = results[0]
    print(f"image={image_path}")
    print(f"preprocessed={preprocess}")
    print("RAW YOLO RESULTS:")
    for box in result.boxes:
        print({
            "class_id": int(box.cls.item()),
            "class": model.names[int(box.cls.item())],
            "confidence": float(box.conf.item()),
            "bbox": [round(value, 2) for value in box.xyxy[0].tolist()],
        })
    print(f"AFTER FILTER confidence>={confidence}:")
    accepted = []
    for box in result.boxes:
        if float(box.conf.item()) >= confidence:
            accepted.append({
                "class": model.names[int(box.cls.item())],
                "confidence": float(box.conf.item()),
                "bbox": [round(value, 2) for value in box.xyxy[0].tolist()],
            })
    print(accepted)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print raw and filtered YOLO predictions for one image.")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--confidence", type=float, default=0.05)
    parser.add_argument("--iou", type=float, default=0.7)
    parser.add_argument("--underwater-preprocess", action="store_true")
    args = parser.parse_args()
    inspect(YOLO(str(args.model)), args.image, args.confidence, args.iou, args.underwater_preprocess)
