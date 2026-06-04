import cv2
import numpy as np
import urllib.request
import os

class PersonDetector:
    def __init__(self):
        self.confidence = 0.5
        self.model_path = "yolov8n.onnx"
        self.net = None
        
        # Try to load ONNX model first
        if os.path.exists(self.model_path):
            try:
                self.net = cv2.dnn.readNetFromONNX(self.model_path)
                print("✅ Using YOLO ONNX model")
                return
            except:
                pass
        
        # Try to download ONNX model
        try:
            print("Downloading YOLOv8 ONNX model (6MB)...")
            url = "https://github.com/ultralytics/ultralytics/releases/download/v8.0.0/yolov8n.onnx"
            urllib.request.urlretrieve(url, self.model_path)
            self.net = cv2.dnn.readNetFromONNX(self.model_path)
            print("✅ ONNX model loaded successfully")
            return
        except Exception as e:
            print(f"⚠️ Could not download ONNX model: {e}")
        
        # Fallback to HOG detector
        print("Using OpenCV HOG fallback detector instead.")
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        self.use_hog = True
        print("💻 Initialized OpenCV HOG person detector")
    
    def detect_people(self, frame):
        if hasattr(self, 'net') and self.net is not None:
            return self._onnx_detect(frame)
        else:
            return self._hog_detect(frame)
    
    def _onnx_detect(self, frame):
        # Prepare input
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (640, 640), swapRB=True, crop=False)
        self.net.setInput(blob)
        outputs = self.net.forward()
        
        # Parse outputs
        people_boxes = []
        h, w = frame.shape[:2]
        
        for detection in outputs[0][0]:
            if len(detection) > 5 and detection[4] > self.confidence:
                if detection[5] == 0:  # person class
                    x1 = int((detection[0] - detection[2]/2) * w)
                    y1 = int((detection[1] - detection[3]/2) * h)
                    x2 = int((detection[0] + detection[2]/2) * w)
                    y2 = int((detection[1] + detection[3]/2) * h)
                    people_boxes.append([x1, y1, x2, y2])
        
        return people_boxes
    
    def _hog_detect(self, frame):
        # Resize for faster processing
        small_frame = cv2.resize(frame, (640, 480))
        
        # Detect people using HOG
        boxes, weights = self.hog.detectMultiScale(
            small_frame, 
            winStride=(4, 4),
            padding=(8, 8),
            scale=1.05
        )
        
        # Scale back to original frame size
        scale_x = frame.shape[1] / 640
        scale_y = frame.shape[0] / 480
        
        people_boxes = []
        for (x, y, w, h) in boxes:
            if len(weights) > 0:
                # Convert to original scale
                x1 = int(x * scale_x)
                y1 = int(y * scale_y)
                x2 = int((x + w) * scale_x)
                y2 = int((y + h) * scale_y)
                people_boxes.append([x1, y1, x2, y2])
        
        return people_boxes
    
    def draw_boxes(self, frame, boxes, ids=None):
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            if ids and i < len(ids):
                cv2.putText(frame, f"ID: {ids[i]}", (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return frame