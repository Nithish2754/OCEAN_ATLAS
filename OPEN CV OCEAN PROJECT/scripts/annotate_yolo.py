from __future__ import annotations

import argparse
from pathlib import Path

import cv2

CLASS_NAMES = [
    "polymetallic_nodules",
    "cobalt_rich_crust",
    "hydrothermal_sulphide",
]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class Annotator:
    def __init__(self, image_path: Path, label_path: Path):
        self.image_path = image_path
        self.label_path = label_path
        self.image = cv2.imread(str(image_path))
        if self.image is None:
            raise RuntimeError(f"Unable to read {image_path}")
        self.boxes = self._read_boxes()
        self.class_id = 0
        self.drag_start: tuple[int, int] | None = None
        self.preview = self.image.copy()
        self.scale = min(1.0, 1200 / self.image.shape[1], 800 / self.image.shape[0])

    def _read_boxes(self) -> list[tuple[int, float, float, float, float]]:
        if not self.label_path.exists():
            return []
        return [
            (int(values[0]), float(values[1]), float(values[2]), float(values[3]), float(values[4]))
            for line in self.label_path.read_text(encoding="utf-8").splitlines()
            if (values := line.split()) and len(values) == 5
        ]

    def _display_point(self, x: int, y: int) -> tuple[int, int]:
        return round(x * self.scale), round(y * self.scale)

    def _image_point(self, x: int, y: int) -> tuple[int, int]:
        return round(x / self.scale), round(y / self.scale)

    def _render(self) -> None:
        display = cv2.resize(self.image, None, fx=self.scale, fy=self.scale)
        height, width = self.image.shape[:2]
        for class_id, center_x, center_y, box_width, box_height in self.boxes:
            x1 = round((center_x - box_width / 2) * width)
            y1 = round((center_y - box_height / 2) * height)
            x2 = round((center_x + box_width / 2) * width)
            y2 = round((center_y + box_height / 2) * height)
            color = [(0, 255, 255), (255, 0, 255), (0, 255, 0)][class_id]
            cv2.rectangle(display, self._display_point(x1, y1), self._display_point(x2, y2), color, 2)
            cv2.putText(display, CLASS_NAMES[class_id], self._display_point(x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
        cv2.putText(display, f"Class {self.class_id}: {CLASS_NAMES[self.class_id]}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.imshow("OceanAtlas YOLO annotation", display)

    def _save(self) -> None:
        self.label_path.parent.mkdir(parents=True, exist_ok=True)
        self.label_path.write_text(
            "".join(f"{class_id} {center_x:.6f} {center_y:.6f} {box_width:.6f} {box_height:.6f}\n" for class_id, center_x, center_y, box_width, box_height in self.boxes),
            encoding="ascii",
        )

    def _mouse(self, event: int, x: int, y: int, _flags: int, _state) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drag_start = self._image_point(x, y)
        elif event == cv2.EVENT_LBUTTONUP and self.drag_start is not None:
            end_x, end_y = self._image_point(x, y)
            start_x, start_y = self.drag_start
            x1, x2 = sorted((max(0, start_x), min(self.image.shape[1], end_x)))
            y1, y2 = sorted((max(0, start_y), min(self.image.shape[0], end_y)))
            if x2 > x1 and y2 > y1:
                width, height = self.image.shape[1], self.image.shape[0]
                self.boxes.append((self.class_id, (x1 + x2) / 2 / width, (y1 + y2) / 2 / height, (x2 - x1) / width, (y2 - y1) / height))
            self.drag_start = None

    def run(self) -> None:
        cv2.namedWindow("OceanAtlas YOLO annotation")
        cv2.setMouseCallback("OceanAtlas YOLO annotation", self._mouse)
        while True:
            self._render()
            key = cv2.waitKey(30) & 0xFF
            if key in (ord("0"), ord("1"), ord("2")):
                self.class_id = key - ord("0")
            elif key == ord("z") and self.boxes:
                self.boxes.pop()
            elif key == ord("c"):
                self.boxes.clear()
            elif key == ord("s"):
                self._save()
                print(f"Saved {self.label_path}")
                break
            elif key == ord("q"):
                break
        cv2.destroyWindow("OceanAtlas YOLO annotation")


def main(source_root: Path, annotations_root: Path) -> None:
    images = sorted(path for path in source_root.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS and "underwater_yolo" not in path.parts)
    for image_path in images:
        relative = image_path.relative_to(source_root)
        label_path = annotations_root / relative.parent / f"{image_path.stem}.txt"
        print(f"Annotating {relative}. Keys: 0/1/2 class, z undo, c clear, s save, q quit")
        Annotator(image_path, label_path).run()
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manually create object-level YOLO labels with OpenCV.")
    parser.add_argument("--source-root", type=Path, default=Path("dataset"))
    parser.add_argument("--annotations-root", type=Path, default=Path("dataset/annotations"))
    args = parser.parse_args()
    main(args.source_root, args.annotations_root)
