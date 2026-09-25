from __future__ import annotations

from ultralytics import YOLO


if __name__ == "__main__":
    model = YOLO("yolov8n.pt")
    model.train(
        data="dataset/underwater_yolo/data.yaml",
        epochs=5,
        imgsz=640,
        batch=8,
        patience=50,
        optimizer="AdamW",
        lr0=0.0005,
        lrf=0.005,
        weight_decay=0.001,
        hsv_h=0.02,
        hsv_s=0.5,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        flipud=0.0,
        mosaic=1.0,
        mixup=0.1,
        close_mosaic=20,
        project="runs",
        name="detect-fixed",
        save=True,
        val=True,
        workers=0,
    )
    print("TRAINING_COMPLETE")
