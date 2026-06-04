import cv2
import numpy as np
import os
import time
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv
from tracker import EuclideanDistTracker
from event_publisher import EventPublisher
from config import (
    API_BASE_URL,
    CAMERA_ID,
    ZONE_ID,
    ENTRY_LINE_Y,
    EXIT_LINE_Y,
    TRACKING_MAX_DISTANCE,
    TRACKING_MAX_DISAPPEARED,
    EVENT_COOLDOWN_SECONDS,
    STAFF_ID_LIST,
    STAFF_PREFIX,
)
import config as cfg

load_dotenv()

EVENTS_ENDPOINT = f"{API_BASE_URL}/events"
last_event_time = defaultdict(float)

def main():
    print("🚀 Starting Motion Detection with Entry/Exit Tracking...")
    
    # Initialize video capture (0 = default webcam)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open webcam")
        return
    
    # Initialize background subtractor
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(
        history=500,
        varThreshold=16,
        detectShadows=False
    )
    
    # Initialize tracker and event publisher
    tracker = EuclideanDistTracker(
        max_distance=TRACKING_MAX_DISTANCE,
        max_disappeared=TRACKING_MAX_DISAPPEARED,
    )
    publisher = EventPublisher(
        EVENTS_ENDPOINT,
        CAMERA_ID,
        ZONE_ID,
        staff_ids=getattr(cfg, 'STAFF_ID_LIST', []),
        staff_prefix=getattr(cfg, 'STAFF_PREFIX', 'staff_'),
    )
    
    # Track previous positions for line crossing detection
    prev_centers = {}
    frame_count = 0
    
    print("🎥 Motion detection started. Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("🏁 Video ended or camera disconnected")
            break
        
        frame_count += 1
        h, w = frame.shape[:2]
        
        # Apply background subtraction
        fg_mask = bg_subtractor.apply(frame)
        
        # Apply morphological operations to clean up the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=2)
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Extract bounding boxes from contours
        boxes = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Filter small noise
                x, y, w_box, h_box = cv2.boundingRect(contour)
                if h_box > 30 and w_box > 30:  # Minimum person-like dimensions
                    boxes.append([x, y, x + w_box, y + h_box])
        
        # Update tracker
        ids = tracker.update(boxes) if boxes else []
        
        # Process events and track crossings
        current_centers = {}
        for i, box in enumerate(boxes):
            if i < len(ids):
                person_id = ids[i]
                center = tracker.get_center(box)
                current_centers[person_id] = center

                if person_id in prev_centers:
                    prev_y = prev_centers[person_id][1]
                    curr_y = center[1]
                    current_time = time.time()

                    if current_time - last_event_time[person_id] >= EVENT_COOLDOWN_SECONDS:
                        if prev_y <= ENTRY_LINE_Y and curr_y > ENTRY_LINE_Y:
                            last_event_time[person_id] = current_time
                            print(f"✅ ENTRY - Person {person_id}")
                            publisher.entry_times[person_id] = datetime.utcnow()
                            publisher.generate_event(person_id, "ENTRY")

                        elif prev_y >= EXIT_LINE_Y and curr_y < EXIT_LINE_Y:
                            last_event_time[person_id] = current_time
                            print(f"❌ EXIT - Person {person_id}")
                            publisher.generate_event(person_id, "EXIT")

        prev_centers = current_centers
        
        # Draw boxes and IDs
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            if i < len(ids):
                person_id = ids[i]
                cv2.putText(
                    frame,
                    f"ID: {person_id}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )
        
        # Draw entry line (green)
        cv2.line(frame, (0, ENTRY_LINE_Y), (w, ENTRY_LINE_Y), (0, 255, 0), 2)
        cv2.putText(
            frame,
            "ENTRY",
            (10, ENTRY_LINE_Y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )
        
        # Draw exit line (red)
        cv2.line(frame, (0, EXIT_LINE_Y), (w, EXIT_LINE_Y), (0, 0, 255), 2)
        cv2.putText(
            frame,
            "EXIT",
            (10, EXIT_LINE_Y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )
        
        # Draw stats
        cv2.putText(
            frame,
            f"People: {len(boxes)} | Frame: {frame_count}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        
        # Display frame
        cv2.imshow("Motion Detection - Entry/Exit Tracking", frame)
        
        # Quit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n🛑 Stopping...")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("✅ Motion detection stopped")


if __name__ == "__main__":
    main()
