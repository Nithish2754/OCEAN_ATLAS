import time
import uuid
import os
import asyncio
from typing import Dict, List, Any

class DetectionStore:
    def __init__(self):
        self.detections: List[Dict[str, Any]] = []
        self.new_detections = asyncio.Queue()
        # Class internal name -> display name
        self.class_map = {
            "polymetallic_nodules": "Polymetallic Nodules",
            "cobalt_rich_crust": "Cobalt-Rich Crusts",
            "hydrothermal_sulphide": "Hydrothermal Sulphides",
            "metal": "Metal"
        }
        self.class_counts: Dict[str, int] = {
            "Polymetallic Nodules": 0,
            "Cobalt-Rich Crusts": 0,
            "Hydrothermal Sulphides": 0,
            "Metal": 0
        }
        # To prevent spam: class name -> timestamp of last recorded detection
        self.last_detection_time: Dict[str, float] = {}
        # Cooldown in seconds
        self.COOLDOWN_SECONDS = 3.0
        
        # Ensure evidence directory exists
        self.evidence_dir = os.path.join(os.path.dirname(__file__), "detection_evidence")
        if not os.path.exists(self.evidence_dir):
            os.makedirs(self.evidence_dir, exist_ok=True)

    def process_detection(self, class_idx: int, class_internal_name: str, confidence: float, bbox: tuple) -> Dict[str, Any]:
        """
        Check if detection should be recorded (cooldown).
        If yes, create a record and return it so yolo_stream can save the image and main can broadcast.
        Returns None if cooling down.
        """
        display_name = self.class_map.get(class_internal_name, class_internal_name)
        now = time.time()
        
        last_time = self.last_detection_time.get(display_name, 0.0)
        if now - last_time < self.COOLDOWN_SECONDS:
            return None # Still in cooldown
            
        # Register new detection
        self.last_detection_time[display_name] = now
        
        # Update counts
        if display_name not in self.class_counts:
            self.class_counts[display_name] = 0
        self.class_counts[display_name] += 1
        
        detection_id = str(uuid.uuid4())
        
        # Create a unique filename for the image evidence
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        filename = f"detection_{timestamp_str}_{detection_id[:8]}.jpg"
        
        detection_record = {
            "id": detection_id,
            "class_name": display_name,
            "confidence": round(confidence * 100, 1), # Percentage
            "timestamp": time.strftime("%H:%M:%S"),
            "image_filename": filename,
            "bounding_box": {
                "x1": int(bbox[0]),
                "y1": int(bbox[1]),
                "x2": int(bbox[2]),
                "y2": int(bbox[3])
            }
        }
        
        self.detections.insert(0, detection_record)
        return detection_record

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_detections": len(self.detections),
            "classes": self.class_counts
        }

    def get_history(self) -> List[Dict[str, Any]]:
        return self.detections

    def reset_session(self):
        self.detections = []
        for k in self.class_counts.keys():
            self.class_counts[k] = 0
        self.last_detection_time = {}

    def delete_detection(self, detection_id: str) -> bool:
        for i, det in enumerate(self.detections):
            if det["id"] == detection_id:
                cls_name = det["class_name"]
                # Update count
                if cls_name in self.class_counts and self.class_counts[cls_name] > 0:
                    self.class_counts[cls_name] -= 1
                
                # Try to delete file
                img_path = os.path.join(self.evidence_dir, det["image_filename"])
                try:
                    if os.path.exists(img_path):
                        os.remove(img_path)
                except Exception as e:
                    print(f"Error deleting image {img_path}: {e}")
                
                # Remove from history
                self.detections.pop(i)
                return True
        return False



# Singleton instance
store = DetectionStore()
