import cv2
import os
from dotenv import load_dotenv
from detector_simple import PersonDetector
from tracker import EuclideanDistTracker
from event_publisher import EventPublisher
from config import STAFF_ID_LIST, STAFF_PREFIX

load_dotenv()

VIDEO_PATH = os.getenv('VIDEO_PATH', '0')
try:
    VIDEO_PATH = int(VIDEO_PATH)
except ValueError:
    pass

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8080/api')
EVENTS_ENDPOINT = f"{API_BASE_URL}/events"
CAMERA_ID = os.getenv('CAMERA_ID', 'ENTRANCE_01')
ZONE_ID = os.getenv('ZONE_ID', 'MAIN_DOOR')
ENTRY_LINE_Y = int(os.getenv('ENTRY_LINE_Y', '300'))
EXIT_LINE_Y = int(os.getenv('EXIT_LINE_Y', '400'))


def main():
    print("🚀 Starting Store Intelligence (Lightweight)...")
    print(f"📹 Video source: {VIDEO_PATH}")

    detector = PersonDetector(confidence=0.5)
    tracker = EuclideanDistTracker()
    publisher = EventPublisher(
        EVENTS_ENDPOINT,
        CAMERA_ID,
        ZONE_ID,
        staff_ids=STAFF_ID_LIST,
        staff_prefix=STAFF_PREFIX,
    )

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"❌ Cannot open: {VIDEO_PATH}")
        return

    prev_centers = {}
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("🏁 Video ended")
            break

        frame_count += 1
        if frame_count % int(os.getenv('FRAME_SKIP', '5')) != 0:
            if prev_centers:
                boxes = []
                frame = detector.draw_boxes(frame, boxes, list(prev_centers.keys()))
            cv2.imshow('Store Intelligence', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

        boxes = detector.detect_people(frame)
        ids = tracker.update(boxes) if boxes else []

        current_centers = {}
        for i, box in enumerate(boxes):
            if i < len(ids):
                current_centers[ids[i]] = tracker.get_center(box)

        for person_id, center in current_centers.items():
            if person_id in prev_centers:
                publisher.process_tracking(
                    person_id,
                    center,
                    prev_centers.get(person_id),
                    ENTRY_LINE_Y,
                    EXIT_LINE_Y,
                )

        prev_centers = current_centers
        frame = detector.draw_boxes(frame, boxes, ids)

        cv2.putText(frame, f"People: {len(boxes)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.line(frame, (0, ENTRY_LINE_Y), (frame.shape[1], ENTRY_LINE_Y), (0, 255, 0), 2)
        cv2.putText(frame, "ENTRY", (10, ENTRY_LINE_Y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.line(frame, (0, EXIT_LINE_Y), (frame.shape[1], EXIT_LINE_Y), (0, 0, 255), 2)
        cv2.putText(frame, "EXIT", (10, EXIT_LINE_Y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        cv2.imshow('Store Intelligence', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("✅ System shutdown")


if __name__ == "__main__":
    main()
