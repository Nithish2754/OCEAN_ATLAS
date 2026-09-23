import cv2
import asyncio
import os
from ultralytics import YOLO
from detection_store import store

# Initialize YOLO model
try:
    # Use the custom trained metal detection model
    model = YOLO("d:/DESKTOP/OPEN CV OCEAN PROJECT/runs/detect/runs/detect-fixed-5/weights/best.pt")
except Exception as e:
    print(f"Error loading custom model: {e}")
    model = YOLO("yolov8n.pt")

async def generate_frames():
    """
    Asynchronous generator that captures webcam frames,
    runs YOLO detection, and yields MJPEG encoded frames.
    """
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print("[YOLO Stream] Error: Could not open webcam.")
        return

    print("[YOLO Stream] Webcam opened successfully.")

    try:
        while True:
            await asyncio.sleep(0.01)

            success, frame = cap.read()
            if not success:
                print("[YOLO Stream] Warning: Failed to read frame from webcam.")
                continue

            # Fine-tuned confidence to 0.46 (just above the 0.449 face false positive)
            # Increased imgsz to 736 to provide the model with higher resolution detail to distinguish the nodule
            results = model.predict(frame, conf=0.46, iou=0.45, imgsz=736, verbose=False)
            
            # Extract detections for logging
            result = results[0]
            boxes = result.boxes
            annotated_frame = result.plot()
            
            has_new_detection = False
            for box in boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = tuple(box.xyxy[0].tolist())
                class_internal_name = result.names[cls_id]
                
                # Check cooldown and record
                det_record = store.process_detection(cls_id, class_internal_name, conf, xyxy)
                if det_record:
                    has_new_detection = True
                    img_path = os.path.join(store.evidence_dir, det_record['image_filename'])
                    cv2.imwrite(img_path, annotated_frame)
                    print(f"[YOLO Stream] Captured evidence: {img_path}")
                    # Push to queue for websocket broadcasting
                    store.new_detections.put_nowait(det_record)

            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            if not ret:
                continue

            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                   
    finally:
        cap.release()
        print("[YOLO Stream] Webcam released.")
