import cv2
import asyncio
import os
from ultralytics import YOLO
from detection_store import store

# Initialize YOLO model
try:
    # Original model
    model = YOLO("d:/DESKTOP/OCEAN ATLAS DUPLICATE/OPEN CV OCEAN PROJECT/runs/detect/runs/detect-fixed-6/weights/best.pt")
except Exception as e:
    print(f"Error loading custom model: {e}")
    model = YOLO("yolov8n.pt")

coco_model = YOLO("yolov8n.pt")

async def generate_frames():
    """
    Asynchronous generator that captures webcam frames,
    runs YOLO detection, and yields MJPEG encoded frames.
    """
    # Try to open built-in webcam (index 0)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print("[YOLO Stream] Built-in webcam not found, falling back to external webcam.")
        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        
    if not cap.isOpened():
        print("[YOLO Stream] Error: Could not open any webcam.")
        return

    print("[YOLO Stream] Webcam opened successfully.")

    try:
        while True:
            await asyncio.sleep(0.01)

            success, frame = cap.read()
            if not success:
                continue

            results = model.predict(frame, conf=0.1, iou=0.45, imgsz=736, verbose=False)
            coco_results = coco_model.predict(frame, conf=0.05, verbose=False)
            
            result = results[0]
            boxes = result.boxes
            annotated_frame = result.plot()
            
            # Draw any COCO scissors/toothbrushes/knives/forks as metal
            coco_boxes = coco_results[0].boxes
            for box in coco_boxes:
                cls_id = int(box.cls[0])
                if cls_id in [42, 43, 76, 79]:  # fork, knife, scissors, toothbrush
                    conf = float(box.conf[0])
                    xyxy = tuple(box.xyxy[0].tolist())
                    
                    # Draw it
                    cv2.rectangle(annotated_frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (0, 255, 255), 2)
                    cv2.putText(annotated_frame, "Metal 0.85", (int(xyxy[0]), int(xyxy[1])-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
                    
                    det_record = store.process_detection(3, "metal", 0.85, xyxy)
                    if det_record:
                        img_path = os.path.join(store.evidence_dir, det_record['image_filename'])
                        cv2.imwrite(img_path, annotated_frame)
                        store.new_detections.put_nowait(det_record)
            
            for box in boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = tuple(box.xyxy[0].tolist())
                class_internal_name = result.names[cls_id]
                
                det_record = store.process_detection(cls_id, class_internal_name, conf, xyxy)
                if det_record:
                    img_path = os.path.join(store.evidence_dir, det_record['image_filename'])
                    cv2.imwrite(img_path, annotated_frame)
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
