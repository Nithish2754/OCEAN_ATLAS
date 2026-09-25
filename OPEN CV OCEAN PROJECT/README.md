# OceanAtlas YOLO Camera Module

This project has been updated to use the 3-class object-detection workflow described in the master prompt:

- polymetallic_nodules
- cobalt_rich_crust
- hydrothermal_sulphide

Rare-earth/sediment detection has been removed from the visual model because it has no reliable object-level visual signature and does not belong in the detector.

## Architecture

- OpenCV handles camera capture and underwater preprocessing
- YOLO handles bounding-box detection, classification, and confidence scoring
- JSON payloads are emitted in a format compatible with the existing backend stream pipeline for `ROV-3-CAM`

## Dataset and annotation layout

Use YOLO-style annotation files, with one `.txt` file per image:

```text
dataset/
  polymetallic_nodules/
  cobalt_rich_crust/
  hydrothermal_sulphides/
  annotations/
  session_manifest.csv
  underwater_yolo/
```

Use `dataset/session_manifest.example.csv` as the required capture-session manifest template. Copy it to `dataset/session_manifest.csv` and replace the example rows with every real image and its capture session/split.

Annotate the source images with the OpenCV tool before preparing the dataset:

```powershell
python scripts\annotate_yolo.py --source-root dataset --annotations-root dataset\annotations
```

In the annotation window, press `0`, `1`, or `2` to select the class, drag around each individual object, press `s` to save, `z` to undo, `c` to clear, and `q` to stop. Empty negative-image label files are valid and must remain empty.

Each source image must have a matching object-level annotation file under `annotations/`, with one line per object. Each annotation line should follow:

```text
class_id x_center y_center width height
```

with values normalized to 0..1.

The preparation script rejects missing labels and the old fabricated full-image label (`0.5 0.5 1.0 1.0`). The session manifest must contain `image,session,split` columns and assign complete capture sessions to `train`, `val`, or `test`; a session cannot cross splits.

## Train a YOLO model

```bash
python scripts/prepare_yolo_dataset.py --manifest dataset/session_manifest.csv --annotations-root dataset/annotations
python scripts/validate_yolo_dataset.py --dataset-root dataset/underwater_yolo
python scripts/audit_dataset.py --dataset-root dataset/underwater_yolo --output runs/evaluation/dataset_audit.json
python scripts/augment_underwater.py --dataset-root dataset/underwater_yolo --factor 2 --balance
# Emergency small-dataset floor: at least 40 effective training images per class.
python scripts/augment_underwater.py --dataset-root dataset/underwater_yolo --factor 2 --target-per-class 40
python -m oceanatlas.train_yolo --data dataset/underwater_yolo/data.yaml --epochs 120 --imgsz 640 --batch 8 --patience 25 --model yolov8n.pt
```

This produces a checkpoint such as `runs/detect/train/weights/best.pt` which should be used in the live run.

## Run the live detector

```bash
python scripts/evaluate_yolo.py --model runs/detect/runs/detect-3/weights/best.pt --data dataset/underwater_yolo/data.yaml --split test
python -m oceanatlas.live_pipeline --camera-index 0 --model-path runs/detect/runs/detect-3/weights/best.pt --confidence 0.05 --stable-frames 3
```

The live pipeline also rejects near-full-frame boxes from legacy checkpoints with `--max-box-area-ratio 0.92`. This is a reliability guard, not a substitute for object-level training.

Compare raw and underwater-preprocessed evaluation before enabling the optional preprocessing flag:

```bash
python scripts/compare_preprocessing.py --model runs/detect/detect/weights/best.pt --dataset-root dataset/underwater_yolo
# Repeat with lighter denoising when texture detail is being lost:
python scripts/compare_preprocessing.py --model runs/detect/detect/weights/best.pt --dataset-root dataset/underwater_yolo --denoise-h 3
```

Use `--underwater-preprocess` only when its held-out test metrics are better than the raw-image result.

Verify and diagnose a known image before using a checkpoint live:

```bash
python scripts/verify_yolo_model.py --model runs/detect/runs/detect-3/weights/best.pt
python scripts/diagnose_yolo_image.py --model runs/detect/runs/detect-3/weights/best.pt --image dataset/polymetallic_nodules/deep-sea-mining-climate-3.jpg --confidence 0.05
```

## Notes

- The training baseline is raw-image YOLO input; underwater preprocessing remains available in the live detector and must be compared against raw-image validation before being enabled for a final model.
- The model emits only the three approved classes and never returns a sediment or fourth class.
- For any real deployment, collect bounded underwater ROV imagery, capture-session metadata, negative examples, and object-level labels with CVAT, LabelImg, or Roboflow before training.
