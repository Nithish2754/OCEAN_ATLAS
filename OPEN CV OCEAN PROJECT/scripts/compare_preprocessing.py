from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import cv2
import yaml
from ultralytics import YOLO

from oceanatlas.preprocessing import preprocess_frame


def _prepare_variant(source_root: Path, destination_root: Path, processed: bool, denoise_h: float) -> None:
    for split in ("train", "val", "test"):
        image_source = source_root / "images" / split
        label_source = source_root / "labels" / split
        image_destination = destination_root / "images" / split
        label_destination = destination_root / "labels" / split
        image_destination.mkdir(parents=True, exist_ok=True)
        label_destination.mkdir(parents=True, exist_ok=True)
        for image_path in image_source.iterdir():
            target = image_destination / image_path.name
            if processed:
                image = cv2.imread(str(image_path))
                if image is None:
                    raise RuntimeError(f"Unable to read {image_path}")
                cv2.imwrite(
                    str(target),
                    preprocess_frame(image, resize_shape=(640, 640), denoise_h=denoise_h, denoise_color_h=denoise_h),
                )
            else:
                shutil.copy2(image_path, target)
            shutil.copy2(label_source / f"{image_path.stem}.txt", label_destination / f"{image_path.stem}.txt")

    source_yaml = yaml.safe_load((source_root / "data.yaml").read_text(encoding="utf-8"))
    (destination_root / "data.yaml").write_text(
        yaml.safe_dump({
            "path": str(destination_root.resolve()).replace("\\", "/"),
            "train": source_yaml["train"],
            "val": source_yaml["val"],
            "test": source_yaml["test"],
            "names": source_yaml["names"],
        }, sort_keys=False),
        encoding="utf-8",
    )


def compare(model_path: Path, dataset_root: Path, denoise_h: float = 10.0) -> dict:
    model = YOLO(str(model_path))
    results = {}
    with tempfile.TemporaryDirectory(prefix="oceanatlas-preprocess-") as temporary:
        temporary_root = Path(temporary)
        for name, processed in (("raw", False), ("underwater_preprocessed", True)):
            variant_root = temporary_root / name
            _prepare_variant(dataset_root, variant_root, processed, denoise_h)
            metrics = model.val(data=str(variant_root / "data.yaml"), split="test", plots=False, verbose=False)
            results[name] = {
                "precision": float(metrics.box.mp),
                "recall": float(metrics.box.mr),
                "mAP50": float(metrics.box.map50),
                "mAP50_95": float(metrics.box.map),
            }
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare raw and underwater-preprocessed YOLO test metrics.")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, default=Path("dataset/underwater_yolo"))
    parser.add_argument("--denoise-h", type=float, default=10.0, help="Denoising strength for the preprocessed variant")
    args = parser.parse_args()
    compare(args.model, args.dataset_root, args.denoise_h)
