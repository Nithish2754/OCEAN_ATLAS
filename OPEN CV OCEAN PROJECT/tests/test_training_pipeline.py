from pathlib import Path

import pytest

from scripts.augment_underwater import _flip_labels, augment_split
from scripts.audit_dataset import count_labels
from scripts.prepare_yolo_dataset import _validate_label_file
from oceanatlas.yolo_pipeline import TemporalDetectionSmoother


def test_full_image_labels_are_rejected(tmp_path: Path):
    label_path = tmp_path / "image.txt"
    label_path.write_text("0 0.5 0.5 1.0 1.0\n", encoding="ascii")
    with pytest.raises(ValueError, match="Full-image"):
        _validate_label_file(label_path)


def test_missing_object_label_is_rejected(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        _validate_label_file(tmp_path / "missing.txt")


def test_dataset_audit_reports_class_image_counts_and_box_geometry(tmp_path: Path):
    label_dir = tmp_path / "labels" / "train"
    label_dir.mkdir(parents=True)
    (label_dir / "crust.txt").write_text("1 0.5 0.5 0.4 0.2\n", encoding="ascii")
    (label_dir / "sulphide.txt").write_text("2 0.5 0.5 0.2 0.4\n", encoding="ascii")

    labels, splits, images, geometry, invalid = count_labels(tmp_path)

    assert labels[1] == 1
    assert labels[2] == 1
    assert splits["train"] == 2
    assert len(images[1]) == 1
    assert geometry[1] == [(0.4, 0.2, 0.08000000000000002)]
    assert not invalid


def test_targeted_augmentation_reaches_requested_class_image_floor(tmp_path: Path):
    image_dir = tmp_path / "images" / "train"
    label_dir = tmp_path / "labels" / "train"
    image_dir.mkdir(parents=True)
    label_dir.mkdir(parents=True)
    import cv2
    import numpy as np

    for class_id, name in ((0, "nodule"), (1, "crust")):
        image_path = image_dir / f"{name}.jpg"
        cv2.imwrite(str(image_path), np.full((16, 16, 3), 80 + class_id, dtype=np.uint8))
        (label_dir / f"{name}.txt").write_text(f"{class_id} 0.5 0.5 0.25 0.25\n", encoding="ascii")

    created = augment_split(tmp_path, factor=0, seed=1, target_per_class=3)

    assert created == 4


def test_horizontal_flip_updates_yolo_x_center():
    assert _flip_labels("0 0.25 0.5 0.2 0.4\n") == "0 0.750000 0.5 0.2 0.4\n"


def test_temporal_smoother_requires_consistent_frames():
    smoother = TemporalDetectionSmoother(stable_frames=3, iou_threshold=0.4)
    detection = {"class": "polymetallic_nodules", "confidence": 0.8, "bbox": [10, 10, 40, 40]}
    assert smoother.update([detection]) == []
    assert smoother.update([detection]) == []
    assert smoother.update([detection]) == [detection]


def test_temporal_smoother_rejects_class_switch():
    smoother = TemporalDetectionSmoother(stable_frames=3, iou_threshold=0.4)
    nodule = {"class": "polymetallic_nodules", "confidence": 0.8, "bbox": [10, 10, 40, 40]}
    crust = {"class": "cobalt_rich_crust", "confidence": 0.8, "bbox": [10, 10, 40, 40]}
    smoother.update([nodule])
    smoother.update([crust])
    assert smoother.update([nodule]) == []
