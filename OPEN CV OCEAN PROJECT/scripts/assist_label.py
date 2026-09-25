import argparse
import subprocess
import sys
from pathlib import Path

from ultralytics import YOLO

CLASS_NAMES = [
    "polymetallic_nodules",
    "cobalt_rich_crust",
    "hydrothermal_sulphide",
]

def generate_suggestions(model_path: Path, pending_dir: Path, labels_dir: Path, class_id: int):
    """Run YOLO on pending images to generate suggested boxes."""
    if not model_path.exists():
        print(f"Warning: Model checkpoint not found at {model_path}. Suggestion generation skipped.")
        return

    print(f"Loading YOLO model from {model_path} for label assistance...")
    model = YOLO(str(model_path))
    
    images = list(pending_dir.glob("*.jpg")) + list(pending_dir.glob("*.png")) + list(pending_dir.glob("*.webp"))
    if not images:
        print(f"No pending images found in {pending_dir}.")
        return

    labels_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating suggested bounding boxes for {len(images)} images...")
    
    for img_path in images:
        label_path = labels_dir / f"{img_path.stem}.txt"
        
        # Don't overwrite if a human already touched it or if we already ran assistance
        if label_path.exists():
            continue
            
        results = model.predict(source=str(img_path), conf=0.05, verbose=False)
        
        with open(label_path, "w", encoding="ascii") as f:
            for result in results:
                # result.boxes.xywhn contains normalized x_center, y_center, width, height
                for box, cls, conf in zip(result.boxes.xywhn, result.boxes.cls, result.boxes.conf):
                    # We'll save ALL detections so the human can review, but we could also
                    # force them to the requested class_id if the model is too wrong.
                    # Given the model collapses, it might predict everything as class 0.
                    # We will keep the model's predicted class so the user sees what the model thought,
                    # but they will have to correct it in the UI.
                    pred_class = int(cls.item())
                    x_c, y_c, w, h = box.tolist()
                    f.write(f"{pred_class} {x_c:.6f} {y_c:.6f} {w:.6f} {h:.6f}\n")

def main(target_class: str, dataset_root: Path, model_path: Path):
    if target_class not in CLASS_NAMES:
        raise ValueError(f"Unknown class {target_class}. Must be one of {CLASS_NAMES}")
        
    class_id = CLASS_NAMES.index(target_class)

    pending_dir = dataset_root / "pending_review" / target_class
    if not pending_dir.exists():
        print(f"No pending review directory found for {target_class}. Run fetch_dataset.py first.")
        return

    # Generate suggestions in a companion labels folder
    labels_dir = dataset_root / "pending_review" / "labels" / target_class
    
    generate_suggestions(model_path, pending_dir, labels_dir, class_id)
    
    # Launch the manual annotator on the pending folder
    print(f"\nLaunching manual annotation tool for {target_class}...")
    print("REVIEW INSTRUCTIONS:")
    print(" - The model's suggestions are pre-loaded.")
    print(" - Press '0', '1', or '2' to set your current active drawing class.")
    print(f"   (0=nodules, 1=crust, 2=sulphide. You are currently reviewing {target_class} which is {class_id})")
    print(" - Drag to draw missing boxes.")
    print(" - Press 'z' to undo the last box.")
    print(" - Press 'c' to clear all boxes (use this if the model's suggestions are totally wrong).")
    print(" - Press 's' to save the corrected boxes and move to the next image.")
    print(" - Press 'q' to quit early.")
    print("-" * 50)
    
    annotator_script = Path("scripts") / "annotate_yolo.py"
    
    subprocess.run([
        sys.executable, str(annotator_script),
        "--source-root", str(dataset_root / "pending_review"),
        "--annotations-root", str(dataset_root / "pending_review" / "labels")
    ])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Model-assisted labeling for fetched images.")
    parser.add_argument("--class-name", type=str, required=True, choices=CLASS_NAMES, help="Target class to review")
    parser.add_argument("--dataset-root", type=Path, default=Path("dataset"), help="Dataset root directory")
    parser.add_argument("--model-path", type=Path, default=Path("runs/detect/runs/detect-3/weights/best.pt"), help="YOLO checkpoint to generate suggestions")
    args = parser.parse_args()
    main(args.class_name, args.dataset_root, args.model_path)
