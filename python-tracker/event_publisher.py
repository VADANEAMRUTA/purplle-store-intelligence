import logging
import requests
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventPublisher:
    def __init__(self, api_url="http://localhost:8080/api/events", camera_id=None, zone_id=None, staff_ids=None, staff_prefix="staff_"):
        self.api_url = api_url
        self.camera_id = camera_id
        self.zone_id = zone_id
        self.staff_ids = set(staff_ids or [])
        self.staff_prefix = staff_prefix
        self.last_entry_positions = {}
        self.last_exit_positions = {}
        self.entry_times = {}
    
    def is_staff_member(self, person_id):
        if person_id is None:
            return False
        if str(person_id).startswith(self.staff_prefix):
            return True
        return str(person_id) in self.staff_ids
    
    def check_line_crossing(self, person_id, current_y, prev_y, line_y, direction):
        """Check if person crossed virtual line"""
        if prev_y is None:
            return False
        
        if direction == 'down':
            return prev_y <= line_y and current_y > line_y
        elif direction == 'up':
            return prev_y >= line_y and current_y < line_y
        
        return False
    
    def generate_event(self, person_id, event_type):
        """Generate and send event to backend"""
        is_staff = self.is_staff_member(person_id)
        event = {
            "personId": str(person_id),
            "eventType": event_type.upper(),
            "event": event_type.upper(),
            "cameraId": self.camera_id,
            "zoneId": self.zone_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "isStaff": is_staff,
            "staffMember": is_staff
        }
        
        if event_type == "EXIT" and person_id in self.entry_times:
            dwell_time = (datetime.utcnow() - self.entry_times[person_id]).seconds
            event["dwellTimeSeconds"] = dwell_time
            del self.entry_times[person_id]
        
        try:
            response = requests.post(
                self.api_url,
                json=event,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Sent {event_type} - Person {person_id}")
                return True
            else:
                logger.error(f"❌ HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            logger.error("❌ Backend not running on port 8080")
            return False
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return False
    
    def process_tracking(self, person_id, current_center, prev_center, entry_line_y, exit_line_y):
        """Process tracking data and generate events on line crossing"""
        if person_id not in self.last_entry_positions:
            self.last_entry_positions[person_id] = None
        if person_id not in self.last_exit_positions:
            self.last_exit_positions[person_id] = None
        
        current_y = current_center[1]
        prev_y = prev_center[1] if prev_center else None
        
        # Check entry line crossing (going down, entering store)
        if self.check_line_crossing(person_id, current_y, prev_y, entry_line_y, 'down'):
            event = self.generate_event(person_id, "ENTRY")
            self.entry_times[person_id] = datetime.utcnow()
            return event
        
        # Check exit line crossing (going up, exiting store)
        if self.check_line_crossing(person_id, current_y, prev_y, exit_line_y, 'up'):
            event = self.generate_event(person_id, "EXIT")
            return event
        
        self.last_entry_positions[person_id] = current_y
        self.last_exit_positions[person_id] = current_y
        
        return None