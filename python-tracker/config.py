import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Video settings
VIDEO_PATH = os.getenv('VIDEO_PATH', '../sample_video/test.mp4')
FRAME_SKIP = int(os.getenv('FRAME_SKIP', '5'))

# Detection settings
CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.5'))
YOLO_MODEL = os.getenv('YOLO_MODEL', 'yolov8n.pt')

# API settings
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8080/api')
EVENTS_ENDPOINT = f"{API_BASE_URL}/events"

# Virtual line position (y-coordinate in pixels)
ENTRY_LINE_Y = int(os.getenv('ENTRY_LINE_Y', '300'))
EXIT_LINE_Y = int(os.getenv('EXIT_LINE_Y', '400'))

# Camera settings
CAMERA_ID = os.getenv('CAMERA_ID', 'ENTRANCE_01')
ZONE_ID = os.getenv('ZONE_ID', 'MAIN_DOOR')

# Tracking parameters
TRACKING_MAX_DISTANCE = int(os.getenv('TRACKING_MAX_DISTANCE', '30'))
TRACKING_MAX_DISAPPEARED = int(os.getenv('TRACKING_MAX_DISAPPEARED', '5'))
EVENT_COOLDOWN_SECONDS = float(os.getenv('EVENT_COOLDOWN_SECONDS', '2.0'))

# Staff exclusion config
STAFF_IDS = os.getenv('STAFF_IDS', '')
STAFF_PREFIX = os.getenv('STAFF_PREFIX', 'staff_')
STAFF_ID_LIST = [item.strip() for item in STAFF_IDS.split(',') if item.strip()]

# Detection parameters
DETECTION_MIN_AREA = int(os.getenv('DETECTION_MIN_AREA', '1000'))
DETECTION_MAX_AREA = int(os.getenv('DETECTION_MAX_AREA', '30000'))
DETECTION_MIN_ASPECT_RATIO = float(os.getenv('DETECTION_MIN_ASPECT_RATIO', '1.5'))
DETECTION_MAX_ASPECT_RATIO = float(os.getenv('DETECTION_MAX_ASPECT_RATIO', '3.5'))

print(f"📹 Config loaded: VIDEO_PATH={VIDEO_PATH}")
print(f"🎯 API URL: {EVENTS_ENDPOINT}")
print(f"🧭 Tracking: max_distance={TRACKING_MAX_DISTANCE}, max_disappeared={TRACKING_MAX_DISAPPEARED}, cooldown={EVENT_COOLDOWN_SECONDS}s")
