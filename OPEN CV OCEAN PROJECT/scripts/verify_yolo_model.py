from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO

EXPECTED_NAMES = {
    0: "polymetallic_nodules",
    1: "cobalt_rich_crust",
    2: "hydrothermal_sulphide",
}


def verify(model_path: Path, confidence: float = 0.05, iou: float = 0.7) -> None:
    model = YOLO(str(model_path))
    names = {int(index): str(name) for index, name in model.names.items()}
    print(f"model_path={model_path.resolve()}")
    print(f"model_type={model.task}")
    print(f"class_count={len(names)}")
    print(f"class_names={names}")
    print(f"confidence_threshold={confidence}")
    print(f"iou_threshold={iou}")
    print(f"model_overrides={model.overrides}")
    if names != EXPECTED_NAMES:
        raise ValueError(f"Checkpoint class mapping is incorrect: {names}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify an OceanAtlas YOLO checkpoint.")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--confidence", type=float, default=0.05)
    parser.add_argument("--iou", type=float, default=0.7)
    args = parser.parse_args()
    verify(args.model, args.confidence, args.iou)
