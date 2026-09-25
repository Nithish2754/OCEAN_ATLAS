from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

CLASS_NAMES = [
    "polymetallic_nodules",
    "cobalt_rich_crust",
    "hydrothermal_sulphide",
]
CLASS_DIRECTORIES = {
    "polymetallic_nodules": Path("dataset/polymetallic_nodules"),
    "cobalt_rich_crust": Path("dataset/cobalt_rich_crust"),
    "hydrothermal_sulphide": Path("dataset/hydrothermal_sulphides"),
}
SPLITS = ("train", "val", "test")


def count_source_images() -> dict[str, int]:
    counts: dict[str, int] = {}
    for class_name, path in CLASS_DIRECTORIES.items():
        if not path.exists():
            counts[class_name] = 0
            continue
        files = [p for p in path.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
        counts[class_name] = len(files)
    return counts


def count_labels(dataset_root: Path) -> tuple[Counter, Counter, dict[int, set[str]], dict[int, list[tuple[float, float, float]]], list[str]]:
    split_counts = Counter()
    label_counts = Counter()
    image_counts: dict[int, set[str]] = defaultdict(set)
    box_geometry: dict[int, list[tuple[float, float, float]]] = defaultdict(list)
    invalid: list[str] = []
    for split in SPLITS:
        for label_file in sorted((dataset_root / "labels" / split).glob("*.txt")):
            image_key = f"{split}/{label_file.stem}"
            split_counts[split] += 1
            for line_number, line in enumerate(label_file.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) != 5:
                    invalid.append(f"{label_file}: invalid fields ({len(parts)}) :: {line}")
                    continue
                try:
                    class_id = int(float(parts[0]))
                    x, y, w, h = [float(v) for v in parts[1:5]]
                except ValueError:
                    invalid.append(f"{label_file}: non-numeric label :: {line}")
                    continue
                label_counts[class_id] += 1
                image_counts[class_id].add(image_key)
                box_geometry[class_id].append((w, h, w * h))
                if w <= 0 or h <= 0:
                    invalid.append(f"{label_file}: zero-sized box :: {line}")
                if w >= 0.999 and h >= 0.999:
                    invalid.append(f"{label_file}: full-image box :: {line}")
                if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 and 0.0 < w <= 1.0 and 0.0 < h <= 1.0):
                    invalid.append(f"{label_file}: out-of-range normalized box :: {line}")
    return label_counts, split_counts, image_counts, box_geometry, invalid


def build_report(dataset_root: Path) -> dict:
    label_counts, split_counts, image_counts, box_geometry, invalid = count_labels(dataset_root)
    classes = {}
    split_classes: dict[str, dict[str, dict[str, int]]] = {}
    for split in SPLITS:
        split_classes[split] = {}
        for class_id, class_name in enumerate(CLASS_NAMES):
            split_dir = dataset_root / "labels" / split
            files = list(split_dir.glob("*.txt"))
            matching_files = [
                path for path in files
                if any(line.strip() and int(float(line.split()[0])) == class_id for line in path.read_text(encoding="utf-8").splitlines())
            ]
            box_count = sum(
                1
                for path in matching_files
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip() and int(float(line.split()[0])) == class_id
            )
            split_classes[split][class_name] = {"image_count": len(matching_files), "box_count": box_count}
    for class_id, class_name in enumerate(CLASS_NAMES):
        boxes = box_geometry.get(class_id, [])
        classes[class_name] = {
            "class_id": class_id,
            "image_count": len(image_counts.get(class_id, set())),
            "box_count": label_counts.get(class_id, 0),
            "mean_width": sum(box[0] for box in boxes) / len(boxes) if boxes else 0.0,
            "mean_height": sum(box[1] for box in boxes) / len(boxes) if boxes else 0.0,
            "mean_area": sum(box[2] for box in boxes) / len(boxes) if boxes else 0.0,
            "mean_aspect": sum(box[0] / box[1] for box in boxes) / len(boxes) if boxes else 0.0,
        }
    return {
        "source_images": count_source_images(),
        "prepared_label_files_by_split": dict(split_counts),
        "class_counts_by_split": split_classes,
        "has_test_split": bool(split_counts.get("test")),
        "classes": classes,
        "invalid_label_count": len(invalid),
    }


def main(dataset_root: Path, output: Path | None = None) -> None:
    source_counts = count_source_images()
    print("SOURCE IMAGE COUNTS")
    for class_name in CLASS_NAMES:
        print(f"  {class_name}: {source_counts.get(class_name, 0)}")

    yaml_lines = (dataset_root / "data.yaml").read_text(encoding="utf-8")
    print("\nDATA.YAML")
    print(yaml_lines)

    label_counts, split_counts, image_counts, box_geometry, invalid = count_labels(dataset_root)
    print("\nCLASS STATISTICS")
    for class_id in range(3):
        boxes = box_geometry.get(class_id, [])
        mean_width = sum(box[0] for box in boxes) / len(boxes) if boxes else 0.0
        mean_height = sum(box[1] for box in boxes) / len(boxes) if boxes else 0.0
        mean_area = sum(box[2] for box in boxes) / len(boxes) if boxes else 0.0
        mean_aspect = sum(box[0] / box[1] for box in boxes) / len(boxes) if boxes else 0.0
        print(
            f"  {CLASS_NAMES[class_id]}: images={len(image_counts.get(class_id, set()))} "
            f"boxes={label_counts.get(class_id, 0)} "
            f"mean_box={mean_width:.3f}x{mean_height:.3f} "
            f"mean_area={mean_area:.3f} mean_aspect={mean_aspect:.3f}"
        )
    print(f"\nLABELED IMAGES BY SPLIT: {dict(split_counts)}")

    print("\nINVALID LABELS")
    if invalid:
        for item in invalid[:20]:
            print(f"  {item}")
        print(f"  total invalid label entries: {len(invalid)}")
    else:
        print("  none found")
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(build_report(dataset_root), indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit the OceanAtlas YOLO dataset and report class imbalance and invalid labels.")
    parser.add_argument("--dataset-root", type=Path, default=Path("dataset/underwater_yolo"))
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON report path")
    args = parser.parse_args()
    main(args.dataset_root, args.output)
