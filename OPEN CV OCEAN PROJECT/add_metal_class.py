import os
import shutil
from pathlib import Path

source_dir = Path("dataset/metal_cutting_blade")
images_train_dir = Path("dataset/underwater_yolo/images/train")
labels_train_dir = Path("dataset/underwater_yolo/labels/train")

for img_path in source_dir.glob("*.jpeg"):
    # Copy image
    dest_img = images_train_dir / img_path.name
    shutil.copy2(img_path, dest_img)
    
    # Create dummy label (class 3, centered, almost full image)
    # format: class_id center_x center_y width height
    label_content = "3 0.5 0.5 0.9 0.9\n"
    label_name = img_path.stem + ".txt"
    dest_label = labels_train_dir / label_name
    dest_label.write_text(label_content)
    
print("Copied images and generated labels.")
