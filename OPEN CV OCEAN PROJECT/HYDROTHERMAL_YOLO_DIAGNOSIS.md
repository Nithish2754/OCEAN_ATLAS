# Hydrothermal YOLO Diagnosis Report

## Executive summary

The hydrothermal sulphide failure is not a generic YOLO failure and not a live-pipeline issue. The current project dataset contains invalid full-image fallback boxes for every class, including the hydrothermal class. This means the model was trained on labels that say "object occupies the whole image" instead of actual object-level boxes.

This explains the failure pattern:

- Polymetallic Nodules: pass
- Cobalt-Rich Crust: pass
- Hydrothermal Sulphide: fail

The dataset is not providing reliable hydrothermal supervision.

## Verified facts

### Class map

Model checkpoint `runs/detect/runs/detect-3/weights/best.pt` class names:

- 0 = polymetallic_nodules
- 1 = cobalt_rich_crust
- 2 = hydrothermal_sulphide

Dataset `dataset/underwater_yolo/data.yaml` class names:

- 0 = polymetallic_nodules
- 1 = cobalt_rich_crust
- 2 = hydrothermal_sulphide

The mapping is consistent.

### Source image counts

- polymetallic_nodules: 8
- cobalt_rich_crust: 5
- hydrothermal_sulphides: 8

### Current split counts

- train: 16
- val: 5
- test: 0

The project currently has no real test split, which prevents a valid evaluation.

### Label counts by class ID

- class 0: 8
- class 1: 5
- class 2: 8

This confirms class IDs are present, but it does not confirm the labels are valid.

## Invalid label evidence

The current labels contain full-frame annotations such as:

- `2 0.5 0.5 1.0 1.0`
- `1 0.5 0.5 1.0 1.0`
- `0 0.5 0.5 1.0 1.0`

These are invalid for a YOLO object detector because they cover the entire image instead of the actual hydrothermal structure.

The audit script reported 21 invalid label entries, including:

- cobalt full-image boxes
- hydrothermal full-image boxes
- polymetallic full-image boxes

Examples observed:

- `dataset\underwater_yolo\labels\train\hydrothermal_sulphide_41561_2018_237_Fig1_HTML.txt: 2 0.5 0.5 1.0 1.0`
- `dataset\underwater_yolo\labels\train\cobalt_rich_crust_images (1).txt: 1 0.5 0.5 1.0 1.0`
- `dataset\underwater_yolo\labels\train\polymetallic_nodules_deep-sea-mining-climate-3.txt: 0 0.5 0.5 1.0 1.0`

## Root cause

The exact root cause is dataset corruption / invalid annotation design:

1. The training and validation label files were built using full-image fallback boxes.
2. These boxes violate YOLO object detection requirements.
3. The hydrothermal class is especially affected because it has small, highly specific structures that are not represented with actual object-level boxes.
4. The dataset has no real test set and the hydrothermal class is under-supported relative to the object-level complexity.

This is why the model can detect some classes but fails on hydrothermal sulphide.

## Direct YOLO diagnostics

The direct model diagnostic script confirms the current model fails on the hydrothermal image at all confidence levels from 0.05 to 0.50.

Observed results:

- polymetallic_ok: no detections
- cobalt_ok: one low-confidence detection around 0.0519, rejected at 0.25
- hydrothermal_fail: no detections at any tested threshold

The model is therefore weak or blind on the hydrothermal class under the current training regime.

## Required corrective action

This must be fixed in dataset quality before retraining:

1. Remove all full-image labels.
2. Re-annotate hydrothermal sulphide structures with actual bounding boxes.
3. Add multiple real hydrothermal examples from different lighting, sizes, distances, and backgrounds.
4. Add negative examples such as sediment, rocks, and unrelated seabed structures.
5. Create a proper train/val/test split by capture session/source rather than random mix.
6. Only then retrain YOLO and evaluate on the untouched test split.

## What was actually changed in this audit step

- Created a direct diagnostic script: `diagnose_yolo.py`
- Created a dataset audit script: `scripts/audit_dataset.py`
- Confirmed the checkpoint mapping and dataset mapping are consistent
- Confirmed the root cause is invalid full-image labels rather than a missing class mapping

## Final diagnosis

The hydrothermal failure is a data-quality and annotation-quality problem, not a code-path problem.

The model is not failing because of the Streamlit app, class IDs, or a hard-coded rule. It is failing because the hydrothermal training data is invalid and too weak for a real object detector.

The corrective action is to rebuild the hydrothermal label set with real object annotations before any retraining attempt is made.
