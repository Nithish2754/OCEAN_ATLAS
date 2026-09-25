import argparse
import csv
import random
import shutil
import time
from pathlib import Path

CLASS_NAMES = [
    "polymetallic_nodules",
    "cobalt_rich_crust",
    "hydrothermal_sulphide",
]

SOURCE_DIRECTORIES = {
    "polymetallic_nodules": "polymetallic_nodules",
    "cobalt_rich_crust": "cobalt_rich_crust",
    "hydrothermal_sulphide": "hydrothermal_sulphides",
}

def main(target_class: str, dataset_root: Path):
    if target_class not in CLASS_NAMES:
        raise ValueError(f"Unknown class {target_class}")

    pending_dir = dataset_root / "pending_review" / target_class
    labels_dir = dataset_root / "pending_review" / "labels" / target_class

    if not labels_dir.exists():
        print(f"No labels directory found at {labels_dir}. Please run assist_label.py first and save your labels.")
        return

    # Map class name to the correct source folder
    dest_img_dir = dataset_root / SOURCE_DIRECTORIES[target_class]
    dest_img_dir.mkdir(parents=True, exist_ok=True)
    
    # We will put the final labels in dataset/annotations/<source_dir_name>
    dest_lbl_dir = dataset_root / "annotations" / SOURCE_DIRECTORIES[target_class]
    dest_lbl_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = dataset_root / "manifest.csv"
    manifest_entries = {}
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                manifest_entries[row["image"].replace("\\", "/")] = row

    # Add any existing raw dataset files to the manifest if they aren't in there yet
    # so we don't lose the original 21 images.
    print("Checking existing dataset images...")
    existing_count = 0
    for cls in CLASS_NAMES:
        folder = dataset_root / SOURCE_DIRECTORIES[cls]
        if folder.exists():
            for img in folder.glob("*"):
                if img.is_file() and img.suffix.lower() in {".jpg", ".png", ".webp", ".jpeg"}:
                    rel_path = f"{SOURCE_DIRECTORIES[cls]}/{img.name}"
                    if rel_path not in manifest_entries:
                        # Existing raw images go to train by default if not previously assigned
                        # but we should randomize them to ensure some val/test exist!
                        r = random.random()
                        split = "train" if r < 0.8 else ("val" if r < 0.9 else "test")
                        manifest_entries[rel_path] = {"image": rel_path, "session": f"legacy_{img.stem}", "split": split}
                        existing_count += 1
    if existing_count > 0:
        print(f"Added {existing_count} pre-existing images to manifest.")

    finalized_count = 0
    # Process reviewed images
    for label_file in labels_dir.glob("*.txt"):
        img_file = pending_dir / f"{label_file.stem}.jpg"
        if not img_file.exists():
            # could be png or webp
            for ext in [".png", ".webp", ".jpeg"]:
                if (pending_dir / f"{label_file.stem}{ext}").exists():
                    img_file = pending_dir / f"{label_file.stem}{ext}"
                    break
                    
        if not img_file.exists():
            print(f"Warning: Label found {label_file.name} but matching image is missing. Skipping.")
            continue
            
        # Check if the label file is completely empty or has NO bounding boxes.
        # It's possible the user opened it and saved it with zero boxes.
        # We only accept images that have at least one bounding box.
        content = label_file.read_text(encoding="utf-8").strip()
        if not content:
            print(f"Skipping {label_file.name} (no bounding boxes).")
            continue

        dest_img_path = dest_img_dir / img_file.name
        dest_lbl_path = dest_lbl_dir / label_file.name
        
        shutil.copy2(img_file, dest_img_path)
        shutil.copy2(label_file, dest_lbl_path)
        
        # Add to manifest
        rel_path = f"{SOURCE_DIRECTORIES[target_class]}/{img_file.name}"
        r = random.random()
        split = "train" if r < 0.8 else ("val" if r < 0.9 else "test")
        
        # We need a unique session id so the prepare script doesn't group all fetched images into the same split
        session_id = f"fetch_{int(time.time())}_{label_file.stem[-8:]}"
        
        manifest_entries[rel_path] = {
            "image": rel_path,
            "session": session_id,
            "split": split
        }
        finalized_count += 1
        
        # Remove from pending so we know it's done
        img_file.unlink()
        label_file.unlink()

    # Rewrite manifest
    with open(manifest_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image", "session", "split"])
        writer.writeheader()
        writer.writerows(manifest_entries.values())

    print(f"\nFinalized {finalized_count} images for {target_class}.")
    print(f"Manifest updated at {manifest_path}")
    print("\nYou can now rebuild the YOLO dataset using:")
    print("python scripts/prepare_yolo_dataset.py --manifest dataset/manifest.csv --annotations-root dataset/annotations")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Finalize pending annotations and add to training set.")
    parser.add_argument("--class-name", type=str, required=True, choices=CLASS_NAMES, help="Target class to finalize")
    parser.add_argument("--dataset-root", type=Path, default=Path("dataset"), help="Dataset root directory")
    args = parser.parse_args()
    main(args.class_name, args.dataset_root)
