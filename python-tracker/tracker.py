import math

class EuclideanDistTracker:
    """Improved tracker using Euclidean distance with persistence and disappearance handling."""

    def __init__(self, max_distance=30, max_disappeared=5):
        self.max_distance = max_distance
        self.max_disappeared = max_disappeared
        self.next_id = 1
        self.objects = {}  # person_id -> {'centroid', 'bbox', 'disappeared', 'last_event_time'}

    def get_center(self, bbox):
        """Get center of bounding box."""
        x1, y1, x2, y2 = bbox
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)
        return (center_x, center_y)

    def euclidean_distance(self, p1, p2):
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def update(self, boxes):
        """Update tracking with new detections and keep object IDs stable."""
        if len(boxes) == 0:
            for object_id in list(self.objects.keys()):
                self.objects[object_id]['disappeared'] += 1
                if self.objects[object_id]['disappeared'] > self.max_disappeared:
                    del self.objects[object_id]
            return []

        centers = [self.get_center(box) for box in boxes]
        detected_ids = [-1] * len(boxes)

        if len(self.objects) == 0:
            for idx, (box, center) in enumerate(zip(boxes, centers)):
                self.objects[self.next_id] = {
                    'centroid': center,
                    'bbox': box,
                    'disappeared': 0,
                    'last_event_time': 0.0
                }
                detected_ids[idx] = self.next_id
                self.next_id += 1
            return detected_ids

        matched_indices = set()
        updated_objects = {}

        for object_id, data in self.objects.items():
            best_distance = float('inf')
            best_index = -1

            for idx, center in enumerate(centers):
                if idx in matched_indices:
                    continue

                dist = self.euclidean_distance(data['centroid'], center)
                if dist < best_distance:
                    best_distance = dist
                    best_index = idx

            if best_index != -1 and best_distance <= self.max_distance:
                detected_ids[best_index] = object_id
                matched_indices.add(best_index)
                updated_objects[object_id] = {
                    'centroid': centers[best_index],
                    'bbox': boxes[best_index],
                    'disappeared': 0,
                    'last_event_time': data.get('last_event_time', 0.0)
                }
            else:
                data['disappeared'] += 1
                if data['disappeared'] <= self.max_disappeared:
                    updated_objects[object_id] = data

        self.objects = updated_objects

        for idx, box in enumerate(boxes):
            if detected_ids[idx] == -1:
                self.objects[self.next_id] = {
                    'centroid': centers[idx],
                    'bbox': box,
                    'disappeared': 0,
                    'last_event_time': 0.0
                }
                detected_ids[idx] = self.next_id
                self.next_id += 1

        return detected_ids

    def get_centroid(self, person_id):
        if person_id in self.objects:
            return self.objects[person_id]['centroid']
        return None