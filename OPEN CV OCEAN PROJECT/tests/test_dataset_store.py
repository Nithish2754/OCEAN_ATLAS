from pathlib import Path

import cv2
import numpy as np

from oceanatlas.dataset import build_feature_store, ensure_dataset_structure


def test_ensure_dataset_structure_creates_class_folders(tmp_path):
    root = tmp_path / "dataset"
    ensure_dataset_structure(root)

    for folder in [
        "polymetallic_nodules",
        "cobalt_rich_crust",
        "hydrothermal_sulphide",
    ]:
        assert (root / folder).exists()


def test_build_feature_store_creates_processed_dataset(tmp_path):
    dataset_root = tmp_path / "dataset"
    ensure_dataset_structure(dataset_root)

    for class_name, color in [
        ("polymetallic_nodules", (40, 60, 80)),
        ("hydrothermal_sulphide", (100, 120, 150)),
        ("cobalt_rich_crust", (30, 40, 60)),
    ]:
        folder = dataset_root / class_name
        for idx in range(2):
            image = np.full((120, 160, 3), color, dtype=np.uint8)
            cv2.imwrite(str(folder / f"{class_name}_{idx}.png"), image)

    output_path = tmp_path / "processed" / "feature_store.npz"
    result = build_feature_store(dataset_root, output_path)

    assert output_path.exists()
    assert result["features"].shape[0] == 6
    assert result["labels"].shape[0] == 6
    assert len(set(result["labels"])) == 3
