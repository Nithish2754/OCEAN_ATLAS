from __future__ import annotations

import argparse
import random
from pathlib import Path

import cv2
import numpy as np

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def augment_image(image: np.ndarray, rng: random.Random) -> tuple[np.ndarray, bool]:
    output = image.astype(np.float32)

    contrast = rng.uniform(0.75, 1.25)
    brightness = rng.uniform(-28.0, 28.0)
    output = output * contrast + brightness

    if rng.random() < 0.8:
        blue_gain = rng.uniform(0.8, 1.15)
        green_gain = rng.uniform(0.9, 1.15)
        output[:, :, 0] *= blue_gain
        output[:, :, 1] *= green_gain

    output = np.clip(output, 0, 255).astype(np.uint8)
    if rng.random() < 0.35:
        output = cv2.GaussianBlur(output, (3, 3), 0)
    if rng.random() < 0.35:
        noise = np.random.default_rng(rng.randint(0, 2**31 - 1)).normal(0, 5, output.shape)
        output = np.clip(output.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    if rng.random() < 0.3:
        output = cv2.convertScaleAbs(output, alpha=0.75, beta=-15)
    flipped = rng.random() < 0.5
    if flipped:
        output = cv2.flip(output, 1)
    return output, flipped


def _flip_labels(label_text: str) -> str:
    flipped_lines = []
    for line in label_text.splitlines():
        values = line.split()
        if not values:
            continue
        values[1] = f"{1.0 - float(values[1]):.6f}"
        flipped_lines.append(" ".join(values))
    return "\n".join(flipped_lines) + ("\n" if flipped_lines else "")


def augment_split(
    root: Path,
    factor: int,
    seed: int = 42,
    balance: bool = False,
    target_per_class: int | None = None,
) -> int:
    rng = random.Random(seed)
    image_dir = root / "images" / "train"
    label_dir = root / "labels" / "train"
    created = 0
    originals = [path for path in image_dir.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS]
    for image_path in originals:
        image = cv2.imread(str(image_path))
        if image is None:
            raise RuntimeError(f"Unable to read {image_path}")
        label_path = label_dir / f"{image_path.stem}.txt"
        for index in range(factor):
            augmented, flipped = augment_image(image, rng)
            output_name = f"{image_path.stem}_aug{index + 1}{image_path.suffix.lower()}"
            cv2.imwrite(str(image_dir / output_name), augmented)
            (label_dir / f"{Path(output_name).stem}.txt").write_text(
                _flip_labels(label_path.read_text(encoding="utf-8")) if flipped else label_path.read_text(encoding="utf-8"),
                encoding="ascii",
            )
            created += 1
    if balance or target_per_class is not None:
        if target_per_class is not None and target_per_class < 1:
            raise ValueError("target_per_class must be positive")
        class_images: dict[int, list[tuple[Path, Path]]] = {}
        for image_path in image_dir.iterdir():
            if "_aug" in image_path.stem or "_balance" in image_path.stem:
                continue
            label_path = label_dir / f"{image_path.stem}.txt"
            labels = label_path.read_text(encoding="utf-8").splitlines()
            for class_id in {int(line.split()[0]) for line in labels if line.strip()}:
                class_images.setdefault(class_id, []).append((image_path, label_path))
        if class_images:
            target = max(len(paths) for paths in class_images.values())
            if target_per_class is not None:
                target = max(target, target_per_class)
            for class_id, paths in class_images.items():
                for index in range(target - len(paths)):
                    image_path, label_path = paths[index % len(paths)]
                    image = cv2.imread(str(image_path))
                    augmented, flipped = augment_image(image, rng)
                    output_name = f"{image_path.stem}_balance{class_id}_{index + 1}{image_path.suffix.lower()}"
                    cv2.imwrite(str(image_dir / output_name), augmented)
                    text = label_path.read_text(encoding="utf-8")
                    (label_dir / f"{Path(output_name).stem}.txt").write_text(
                        _flip_labels(text) if flipped else text,
                        encoding="ascii",
                    )
                    created += 1
    return created


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create deterministic underwater training augmentations.")
    parser.add_argument("--dataset-root", type=Path, default=Path("dataset/underwater_yolo"))
    parser.add_argument("--factor", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--balance", action="store_true", help="Augment underrepresented labeled classes toward the largest class")
    parser.add_argument(
        "--target-per-class",
        type=int,
        default=None,
        help="Create at least this many augmented training images per labeled class",
    )
    args = parser.parse_args()
    print(
        f"Created {augment_split(args.dataset_root, args.factor, args.seed, args.balance, args.target_per_class)} "
        "augmented training images."
    )
