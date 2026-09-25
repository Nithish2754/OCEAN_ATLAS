from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import cv2

from .dataset import CLASS_NAMES, ensure_dataset_structure


def capture_frames_for_class(
    dataset_root: str | Path,
    class_name: str,
    camera_index: int = 0,
    max_images: int = 20,
    save_interval: float = 1.0,
):
    if class_name not in CLASS_NAMES:
        raise ValueError(f"Unsupported class '{class_name}'. Supported classes: {CLASS_NAMES}")

    root = ensure_dataset_structure(dataset_root)
    class_dir = root / class_name
    class_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open camera index {camera_index}.")

    count = 0
    print(f"Starting capture for '{class_name}' into {class_dir}...")
    print("Press 's' to save the current frame, 'q' to quit.")

    while count < max_images:
        success, frame = cap.read()
        if not success or frame is None:
            continue

        cv2.imshow(f"Capture {class_name}", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            output_path = class_dir / f"{class_name}_{timestamp}.jpg"
            cv2.imwrite(str(output_path), frame)
            count += 1
            print(f"Saved {count}/{max_images}: {output_path}")

        if key == ord("q"):
            break

        if save_interval > 0:
            # keep the loop responsive; a user can also press s for manual capture
            pass

    cap.release()
    cv2.destroyAllWindows()
    print(f"Finished capture for '{class_name}'. Total stored: {count}")
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture real underwater seafloor photos into the dataset folders.")
    parser.add_argument("--dataset-root", type=str, default="dataset", help="Folder containing the class directories")
    parser.add_argument("--class-name", type=str, required=True, choices=CLASS_NAMES, help="Target deposit class to capture")
    parser.add_argument("--camera-index", type=int, default=0, help="OpenCV video capture index")
    parser.add_argument("--max-images", type=int, default=20, help="Number of images to collect for this class")
    args = parser.parse_args()

    capture_frames_for_class(
        dataset_root=args.dataset_root,
        class_name=args.class_name,
        camera_index=args.camera_index,
        max_images=args.max_images,
    )
