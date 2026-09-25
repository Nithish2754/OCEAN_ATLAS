from __future__ import annotations

import argparse
from pathlib import Path

import cv2

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def infer_class_id(filename: str) -> int:
    text = filename.lower()
    if "polymetallic" in text or "nodule" in text:
        return 0
    if "cobalt" in text or "crust" in text:
        return 1
    if "hydrothermal" in text or "sulphide" in text or "sulfide" in text:
        return 2
    raise ValueError(f"Unable to infer class ID from '{filename}'")


def estimate_object_box(image_path: Path) -> tuple[float, float, float, float]:
    image = cv2.imread(str(image_path))
    if image is None:
        raise RuntimeError(f"Unable to read image: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise RuntimeError(f"No object contour found in {image_path}; manual annotation required.")
    contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(contour)
    if area < 200:
        raise RuntimeError(f"Object contour is too small for {image_path}; manual annotation required.")

    x, y, w, h = cv2.boundingRect(contour)
    height, width = image.shape[:2]
    pad = max(8, min(w, h) // 6)
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(width, x + w + pad)
    y2 = min(height, y + h + pad)
    box_w = float(x2 - x1)
    box_h = float(y2 - y1)
    if box_w / width > 0.95 or box_h / height > 0.95:
        margin_x = max(0.05 * width, 20.0)
        margin_y = max(0.05 * height, 20.0)
        x1 = int(max(0, width * 0.1))
        y1 = int(max(0, height * 0.1))
        x2 = int(min(width, width * 0.9))
        y2 = int(min(height, height * 0.9))
        box_w = float(x2 - x1)
        box_h = float(y2 - y1)
        center_x = (x1 + x2) / 2.0 / width
        center_y = (y1 + y2) / 2.0 / height
        normalized_w = box_w / width
        normalized_h = box_h / height
        return center_x, center_y, normalized_w, normalized_h

    center_x = (x1 + x2) / 2.0 / width
    center_y = (y1 + y2) / 2.0 / height
    normalized_w = box_w / width
    normalized_h = box_h / height
    return center_x, center_y, normalized_w, normalized_h


def repair_dataset(dataset_root: Path) -> None:
    for split in ("train", "val"):
        split_dir = dataset_root / "images" / split
        if not split_dir.exists():
            continue
        for image_path in sorted(split_dir.iterdir()):
            if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            label_path = dataset_root / "labels" / split / f"{image_path.stem}.txt"
            class_id = infer_class_id(image_path.name)
            center_x, center_y, w, h = estimate_object_box(image_path)
            label_path.parent.mkdir(parents=True, exist_ok=True)
            label_path.write_text(f"{class_id} {center_x:.6f} {center_y:.6f} {w:.6f} {h:.6f}\n", encoding="ascii")
            print(f"{image_path} -> {label_path} :: {class_id} {center_x:.6f} {center_y:.6f} {w:.6f} {h:.6f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert whole-image fallback labels into normalized object boxes for the underwater YOLO dataset.")
    parser.add_argument("--dataset-root", type=Path, default=Path("dataset/underwater_yolo"))
    args = parser.parse_args()
    repair_dataset(args.dataset_root)
