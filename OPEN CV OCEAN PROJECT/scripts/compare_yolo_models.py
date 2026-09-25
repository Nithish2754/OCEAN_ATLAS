from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


def evaluate(model_path: Path, data: Path, split: str) -> dict:
    model = YOLO(str(model_path))
    metrics = model.val(data=str(data), split=split, plots=False, verbose=False)
    return {
        "model": str(model_path),
        "precision": float(metrics.box.mp),
        "recall": float(metrics.box.mr),
        "mAP50": float(metrics.box.map50),
        "mAP50_95": float(metrics.box.map),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare YOLO checkpoints on exactly the same split.")
    parser.add_argument("--data", type=Path, default=Path("dataset/underwater_yolo/data.yaml"))
    parser.add_argument("--split", choices=("val", "test"), default="test")
    parser.add_argument("--model", type=Path, action="append", required=True)
    args = parser.parse_args()
    for model_path in args.model:
        print(evaluate(model_path, args.data, args.split))
