import requests
from datetime import datetime

API_ROOT = "http://localhost:8080/api"

print("Testing backend health...")
try:
    r = requests.get(f"{API_ROOT}/health", timeout=5)
    print(f"Health: {r.status_code} - {r.text}")
except Exception as e:
    print(f"Health check failed: {e}")

print("\nTesting event POST...")
event = {
    "personId": "test_001",
    "eventType": "ENTRY",
    "timestamp": datetime.now().isoformat(),
    "cameraId": "camera_test",
    "zoneId": "zone_test"
}
try:
    r = requests.post(f"{API_ROOT}/events", json=event, timeout=5)
    print(f"Post: {r.status_code} - {r.text}")
except Exception as e:
    print(f"Event post failed: {e}")

print("\nTesting recent events retrieval...")
try:
    r = requests.get(f"{API_ROOT}/events/recent", timeout=5)
    body = r.text if r.text else 'empty'
    print(f"Events: {r.status_code} - {body[:200]}")
except Exception as e:
    print(f"Event retrieval failed: {e}")
