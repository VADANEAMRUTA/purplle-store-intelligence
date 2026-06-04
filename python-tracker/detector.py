import cv2
from ultralytics import YOLO
from config import (
    CONFIDENCE_THRESHOLD,
    DETECTION_MIN_AREA,
    DETECTION_MAX_AREA,
    DETECTION_MIN_ASPECT_RATIO,
    DETECTION_MAX_ASPECT_RATIO,
)

class PersonDetector:
    def __init__(self, model_name='yolov8n.pt', confidence=None):
        self.model = YOLO(model_name)
        self.confidence = confidence if confidence is not None else CONFIDENCE_THRESHOLD
        
        if cv2.cuda.getCudaEnabledDeviceCount():
            print("🚀 CUDA available - using GPU")
            self.model.to('cuda')
        else:
            print("💻 Using CPU")
    
    def detect_people(self, frame):
        """Detect people in frame and return filtered bounding boxes."""
        results = self.model(frame, conf=self.confidence, verbose=False)
        people_boxes = []

        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    if int(box.cls[0]) != 0:
                        continue

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    width = x2 - x1
                    height = y2 - y1
                    area = width * height
                    aspect_ratio = height / max(width, 1)

                    if (
                        DETECTION_MIN_AREA <= area <= DETECTION_MAX_AREA
                        and DETECTION_MIN_ASPECT_RATIO <= aspect_ratio <= DETECTION_MAX_ASPECT_RATIO
                        and width > 30
                        and height > 60
                    ):
                        people_boxes.append([x1, y1, x2, y2])

        return people_boxes
    
    def draw_boxes(self, frame, boxes, ids=None):
        """Draw bounding boxes and IDs on frame"""
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            if ids and i < len(ids):
                cv2.putText(frame, f"ID: {ids[i]}", (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return frame