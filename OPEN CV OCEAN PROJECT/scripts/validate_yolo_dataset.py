from __future__ import annotations

import argparse
import hashlib
from collections import Counter
from pathlib import Path

import cv2
import yaml


def validate(dataset_root: Path) -> int:
    data = yaml.safe_load((dataset_root / "data.yaml").read_text(encoding="utf-8"))
    names = data["names"]
    errors: list[str] = []
    hashes: dict[str, Path] = {}
    totals = Counter()
    for split in ("train", "val", "test"):
        image_dir = dataset_root / "images" / split
        label_dir = dataset_root / "labels" / split
        if not image_dir.exists():
            errors.append(f"missing image directory: {image_dir}")
            continue
        for image_path in image_dir.iterdir():
            if not image_path.is_file():
                continue
            image = cv2.imread(str(image_path))
            if image is None:
                errors.append(f"corrupt image: {image_path}")
                continue
            digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
            if digest in hashes:
                errors.append(f"duplicate image: {image_path} and {hashes[digest]}")
            hashes[digest] = image_path
            label_path = label_dir / f"{image_path.stem}.txt"
            if not label_path.exists():
                errors.append(f"missing label: {label_path}")
                continue
            for line_number, line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), 1):
                values = line.split()
                if len(values) != 5:
                    errors.append(f"invalid field count: {label_path}:{line_number}")
                    continue
                class_id, center_x, center_y, width, height = map(float, values)
                if int(class_id) != class_id or int(class_id) not in names:
                    errors.append(f"invalid class id: {label_path}:{line_number}")
                if not all(0.0 <= value <= 1.0 for value in (center_x, center_y, width, height)):
                    errors.append(f"out-of-range coordinate: {label_path}:{line_number}")
                if width <= 0 or height <= 0:
                    errors.append(f"zero-sized box: {label_path}:{line_number}")
                totals[int(class_id)] += 1
    print(f"images={len(hashes)}")
    print(f"objects_by_class={dict(totals)}")
    print(f"errors={len(errors)}")
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate YOLO images, labels, duplicates, and class IDs.")
    parser.add_argument("--dataset-root", type=Path, default=Path("dataset/underwater_yolo"))
    args = parser.parse_args()
    raise SystemExit(validate(args.dataset_root))
