from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def _validate_training_labels(data_yaml: str) -> None:
    data_path = Path(data_yaml)
    data = yaml.safe_load(data_path.read_text(encoding="utf-8"))
    root = Path(data.get("path", data_path.parent))
    if not root.is_absolute():
        root = Path.cwd() / root
    label_root = root / str(data["train"]).replace("images", "labels", 1)
    for label_path in label_root.rglob("*.txt"):
        for line in label_path.read_text(encoding="utf-8").splitlines():
            values = line.split()
            if len(values) == 5 and float(values[3]) >= 0.999 and float(values[4]) >= 0.999:
                raise ValueError(
                    f"Refusing to train with full-image fallback label: {label_path}. "
                    "Run scripts\\annotate_yolo.py and scripts\\prepare_yolo_dataset.py first."
                )


def train_yolo(
    data_yaml: str,
    model: str = "yolov8n.pt",
    epochs: int = 120,
    imgsz: int = 640,
    batch: int = 8,
    patience: int = 25,
):
    try:
        from ultralytics import YOLO
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("ultralytics is not installed. Install requirements before training YOLO.") from exc

    _validate_training_labels(data_yaml)
    model_obj = YOLO(model)
    results = model_obj.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        patience=patience,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        weight_decay=0.0005,
        hsv_h=0.02,
        hsv_s=0.45,
        hsv_v=0.35,
        degrees=3.0,
        translate=0.08,
        scale=0.35,
        fliplr=0.5,
        flipud=0.0,
        mosaic=0.25,
        mixup=0.05,
        close_mosaic=15,
        project="runs",
        name="detect",
        save=True,
        val=True,
    )
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the OceanAtlas YOLO detector on the 3-class underwater dataset.")
    parser.add_argument("--data", type=str, required=True, help="Path to the dataset data.yaml file")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="Pretrained checkpoint to fine-tune")
    parser.add_argument("--epochs", type=int, default=120, help="Maximum training epochs")
    parser.add_argument("--imgsz", type=int, default=640, help="Input image size")
    parser.add_argument("--batch", type=int, default=8, help="Batch size; reduce for CPU or limited RAM")
    parser.add_argument("--patience", type=int, default=25, help="Early-stopping patience")
    args = parser.parse_args()
    train_yolo(args.data, args.model, args.epochs, args.imgsz, args.batch, args.patience)
