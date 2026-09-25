from __future__ import annotations

import argparse
import csv
import shutil
from collections import defaultdict
from pathlib import Path

SOURCE_ROOT = Path("dataset")
OUTPUT_ROOT = Path("dataset/underwater_yolo")
CLASS_NAMES = [
    "polymetallic_nodules",
    "cobalt_rich_crust",
    "hydrothermal_sulphide",
]
SOURCE_DIRECTORIES = {
    "polymetallic_nodules": "polymetallic_nodules",
    "cobalt_rich_crust": "cobalt_rich_crust",
    "hydrothermal_sulphide": "hydrothermal_sulphides",
}
NEGATIVE_DIRECTORIES = ("plain_sediment_unclassified",)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SPLITS = ("train", "val", "test")


def _read_manifest(manifest_path: Path) -> dict[str, dict[str, str]]:
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Session manifest not found: {manifest_path}. Create a CSV with image,session,split columns."
        )
    with manifest_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = csv.DictReader(handle)
        required = {"image", "session", "split"}
        if not required.issubset(rows.fieldnames or set()):
            raise ValueError("Session manifest must contain image,session,split columns.")
        manifest = {}
        for row in rows:
            split = row["split"].strip().lower()
            if split not in SPLITS:
                raise ValueError(f"Unsupported split '{split}' for {row['image']}")
            manifest[row["image"].replace("\\", "/")] = {
                "session": row["session"].strip(),
                "split": split,
            }
        return manifest


def _label_path(image_path: Path, annotations_root: Path) -> Path:
    relative = image_path.relative_to(SOURCE_ROOT)
    return annotations_root / relative.parent / f"{image_path.stem}.txt"


def _validate_label_file(label_path: Path, class_count: int = 3) -> None:
    if not label_path.exists():
        raise FileNotFoundError(
            f"Missing object-level YOLO annotation: {label_path}. "
            "Do not use full-image fallback labels; annotate each object with CVAT, LabelImg, or Roboflow."
        )
    for line_number, line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), 1):
        values = line.split()
        if not values:
            continue
        if len(values) != 5:
            raise ValueError(f"Invalid YOLO label at {label_path}:{line_number}; expected 5 values.")
        class_id, *coordinates = map(float, values)
        if class_id != int(class_id) or not 0 <= int(class_id) < class_count:
            raise ValueError(f"Invalid class id at {label_path}:{line_number}.")
        if not all(0.0 <= value <= 1.0 for value in coordinates):
            raise ValueError(f"YOLO coordinates must be normalized at {label_path}:{line_number}.")
        _, _, width, height = coordinates
        if width >= 0.999 and height >= 0.999:
            raise ValueError(
                f"Full-image fallback annotation found at {label_path}:{line_number}; "
                "use object-level boxes instead."
            )


def _collect_images() -> list[Path]:
    images = []
    for class_name in CLASS_NAMES:
        source_dir = SOURCE_ROOT / SOURCE_DIRECTORIES[class_name]
        images.extend(path for path in source_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
    for directory in NEGATIVE_DIRECTORIES:
        source_dir = SOURCE_ROOT / directory
        if source_dir.exists():
            images.extend(path for path in source_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
    return sorted(images)


def main(source_root: Path = SOURCE_ROOT, output_root: Path = OUTPUT_ROOT, manifest_path: Path | None = None, annotations_root: Path | None = None) -> None:
    global SOURCE_ROOT, OUTPUT_ROOT
    SOURCE_ROOT = source_root
    OUTPUT_ROOT = output_root
    annotations_root = annotations_root or source_root
    if manifest_path is None:
        raise ValueError("A capture-session manifest is required; use --manifest.")
    manifest = _read_manifest(manifest_path)

    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    for split in SPLITS:
        (OUTPUT_ROOT / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUTPUT_ROOT / "labels" / split).mkdir(parents=True, exist_ok=True)

    session_splits: dict[str, str] = {}
    split_counts = defaultdict(int)
    for image_path in _collect_images():
        relative = image_path.relative_to(SOURCE_ROOT).as_posix()
        entry = manifest.get(relative)
        if entry is None:
            raise ValueError(f"Image missing from session manifest: {relative}")
        previous = session_splits.setdefault(entry["session"], entry["split"])
        if previous != entry["split"]:
            raise ValueError(f"Capture session '{entry['session']}' appears in multiple splits.")
        source_label = _label_path(image_path, annotations_root)
        if image_path.parent.name in NEGATIVE_DIRECTORIES and not source_label.exists():
            source_label.parent.mkdir(parents=True, exist_ok=True)
            source_label.write_text("", encoding="ascii")
        _validate_label_file(source_label)
        destination_name = f"{image_path.parent.name}_{image_path.name}"
        destination = OUTPUT_ROOT / "images" / entry["split"] / destination_name
        shutil.copy2(image_path, destination)
        shutil.copy2(source_label, OUTPUT_ROOT / "labels" / entry["split"] / f"{destination.stem}.txt")
        split_counts[entry["split"]] += 1

    if not split_counts["train"] or not split_counts["val"] or not split_counts["test"]:
        raise ValueError("Manifest must provide non-empty train, val, and test capture-session splits.")

    yaml_path = OUTPUT_ROOT / "data.yaml"
    yaml_path.write_text(
        "path: dataset/underwater_yolo\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n"
        "names:\n"
        "  0: polymetallic_nodules\n"
        "  1: cobalt_rich_crust\n"
        "  2: hydrothermal_sulphide\n",
        encoding="ascii",
    )
    print(f"Prepared YOLO dataset at {OUTPUT_ROOT}")
    print(f"Training images: {split_counts['train']}")
    print(f"Validation images: {split_counts['val']}")
    print(f"Test images: {split_counts['test']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare an annotated, session-split YOLO dataset.")
    parser.add_argument("--source-root", type=Path, default=SOURCE_ROOT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--manifest", type=Path, required=True, help="CSV with image,session,split columns")
    parser.add_argument("--annotations-root", type=Path, default=None, help="Root containing object-level YOLO txt files")
    args = parser.parse_args()
    main(args.source_root, args.output_root, args.manifest, args.annotations_root)
