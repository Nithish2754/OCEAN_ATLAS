from __future__ import annotations

import argparse
import json
from pathlib import Path

from ultralytics import YOLO


CLASS_NAMES = [
    "polymetallic_nodules",
    "cobalt_rich_crust",
    "hydrothermal_sulphide",
]


def _values(values) -> list[float]:
    return [float(value) for value in values]


def evaluate(model_path: Path, data_yaml: Path, split: str = "test", output: Path | None = None) -> dict:
    model = YOLO(str(model_path))
    results = model.val(
        data=str(data_yaml),
        split=split,
        plots=True,
        verbose=False,
    )
    box = results.box
    metrics = {
        "model": str(model_path),
        "data": str(data_yaml),
        "split": split,
        "precision": float(box.mp),
        "recall": float(box.mr),
        "mAP50": float(box.map50),
        "mAP50_95": float(box.map),
        "per_class": {
            name: {
                "precision": precision,
                "recall": recall,
                "mAP50": map50,
                "mAP50_95": map95,
            }
            for name, precision, recall, map50, map95 in zip(
                CLASS_NAMES,
                _values(box.p),
                _values(box.r),
                _values(box.ap50),
                _values(box.ap),
            )
        },
        "confusion_matrix": str(Path(results.save_dir) / "confusion_matrix.png"),
    }
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate an OceanAtlas YOLO checkpoint on the held-out test split.")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=Path("dataset/underwater_yolo/data.yaml"))
    parser.add_argument("--split", choices=("val", "test"), default="test")
    parser.add_argument("--output", type=Path, default=Path("runs/evaluation/test_metrics.json"))
    args = parser.parse_args()
    evaluate(args.model, args.data, args.split, args.output)
