import cv2
import os
from dotenv import load_dotenv
from detector import PersonDetector
from tracker import EuclideanDistTracker
from event_publisher import EventPublisher

# Load environment variables
load_dotenv()

# Get configuration
VIDEO_PATH = os.getenv('VIDEO_PATH', '0')
try:
    VIDEO_PATH = int(VIDEO_PATH)
except ValueError:
    pass

FRAME_SKIP = int(os.getenv('FRAME_SKIP', '5'))
CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.5'))
YOLO_MODEL = os.getenv('YOLO_MODEL', 'yolov8n.pt')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8080/api')
EVENTS_ENDPOINT = f"{API_BASE_URL}/events"
ENTRY_LINE_Y = int(os.getenv('ENTRY_LINE_Y', '300'))
EXIT_LINE_Y = int(os.getenv('EXIT_LINE_Y', '400'))
CAMERA_ID = os.getenv('CAMERA_ID', 'ENTRANCE_01')
ZONE_ID = os.getenv('ZONE_ID', 'MAIN_DOOR')

def main():
    print("🚀 Starting Store Intelligence System...")
    print(f"📹 Video source: {VIDEO_PATH}")
    
    # Initialize components
    detector = PersonDetector(YOLO_MODEL, CONFIDENCE_THRESHOLD)
    tracker = EuclideanDistTracker()
    publisher = EventPublisher(
        EVENTS_ENDPOINT,
        CAMERA_ID,
        ZONE_ID,
        staff_ids=STAFF_ID_LIST,
        staff_prefix=STAFF_PREFIX,
    )
    
    # Open video capture
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"❌ Cannot open video source: {VIDEO_PATH}")
        return
    
    prev_boxes = []
    prev_centers = {}
    frame_count = 0
    
    print("🎥 Processing... Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("🏁 Video ended")
            break
        
        frame_count += 1
        
        # Skip frames for performance
        if frame_count % FRAME_SKIP != 0:
            if prev_boxes:
                frame = detector.draw_boxes(frame, prev_boxes, list(prev_centers.keys()))
            
            # Draw virtual lines
            cv2.line(frame, (0, ENTRY_LINE_Y), (frame.shape[1], ENTRY_LINE_Y), (0, 255, 0), 2)
            cv2.putText(frame, "ENTRY", (10, ENTRY_LINE_Y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
            cv2.line(frame, (0, EXIT_LINE_Y), (frame.shape[1], EXIT_LINE_Y), (0, 0, 255), 2)
            cv2.putText(frame, "EXIT", (10, EXIT_LINE_Y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
            
            cv2.imshow('Store Intelligence', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue
        
        # Detect people
        boxes = detector.detect_people(frame)
        
        if len(boxes) > 0:
            ids = tracker.update(boxes)
            
            current_centers = {}
            for i, box in enumerate(boxes):
                if i < len(ids):
                    current_centers[ids[i]] = tracker.get_center(box)
            
            # Process events
            for person_id in current_centers:
                if person_id in prev_centers:
                    event = publisher.process_tracking(
                        person_id, 
                        current_centers[person_id],
                        prev_centers.get(person_id),
                        ENTRY_LINE_Y, 
                        EXIT_LINE_Y
                    )
            
            prev_centers = current_centers
            prev_boxes = boxes
            frame = detector.draw_boxes(frame, boxes, ids)
        else:
            prev_boxes = []
        
        # Draw lines and info
        cv2.line(frame, (0, ENTRY_LINE_Y), (frame.shape[1], ENTRY_LINE_Y), (0, 255, 0), 2)
        cv2.line(frame, (0, EXIT_LINE_Y), (frame.shape[1], EXIT_LINE_Y), (0, 0, 255), 2)
        cv2.putText(frame, f"People: {len(boxes)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        
        cv2.imshow('Store Intelligence', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("✅ System shutdown")

if __name__ == "__main__":
    main()