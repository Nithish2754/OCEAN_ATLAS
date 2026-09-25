from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from .features import extract_frame_features

CLASS_NAMES = [
    "polymetallic_nodules",
    "cobalt_rich_crust",
    "hydrothermal_sulphide",
]


def ensure_dataset_structure(dataset_root: str | Path):
    root = Path(dataset_root)
    root.mkdir(parents=True, exist_ok=True)
    for folder in CLASS_NAMES:
        (root / folder).mkdir(parents=True, exist_ok=True)
    return root


def collect_dataset_images(dataset_root: str | Path):
    root = Path(dataset_root)
    image_rows = []
    labels = []

    for label in CLASS_NAMES:
        class_dir = root / label
        if not class_dir.exists():
            continue
        for image_file in sorted(class_dir.iterdir()):
            if image_file.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp", ".tif"}:
                continue
            frame = cv2.imread(str(image_file))
            if frame is None:
                continue
            image_rows.append(frame)
            labels.append(label)

    if not image_rows:
        raise ValueError(f"No usable image files were found under dataset root: {root}")

    return image_rows, labels


def build_feature_store(dataset_root: str | Path, output_path: str | Path | None = None):
    images, labels = collect_dataset_images(dataset_root)
    features = []

    for frame in images:
        features.append(extract_frame_features(frame))

    stacked = np.vstack(features)
    label_array = np.asarray(labels)

    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, features=stacked, labels=label_array, class_names=np.asarray(CLASS_NAMES))

    return {"features": stacked, "labels": label_array, "class_names": np.asarray(CLASS_NAMES)}


def save_dataset_manifest(dataset_root: str | Path, output_path: str | Path):
    root = Path(dataset_root)
    manifest = []
    for label in CLASS_NAMES:
        class_dir = root / label
        if not class_dir.exists():
            continue
        for image_file in sorted(class_dir.iterdir()):
            if image_file.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp", ".tif"}:
                continue
            manifest.append({
                "class": label,
                "path": str(image_file.relative_to(root)),
                "filename": image_file.name,
            })

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    return manifest
