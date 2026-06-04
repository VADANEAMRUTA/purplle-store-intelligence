# Purplle Store Intelligence System Design

## Architecture Overview
The system is composed of two main subsystems:
- `python-tracker`: Python-based video analytics pipeline that performs person detection, tracking, line-crossing detection, and event publishing.
- `spring-boot-api`: Java Spring Boot backend that receives events, persists them to H2 database, writes a JSONL audit log, and serves dashboard analytics and user management APIs.

## Components

### Python Tracker
- Uses Ultralytics YOLOv8 for person detection.
- Uses a simple Euclidean tracker to assign stable IDs across frames.
- Defines virtual entry and exit lines inside the video frame.
- Publishes `ENTRY` and `EXIT` events to the REST API.
- Marks staff members using either configured `STAFF_IDS` or `STAFF_PREFIX` so staff traffic is excluded from occupancy/footfall analytics.

### Spring Boot API
- Exposes REST endpoints under `/api`:
  - `POST /api/events`: ingest event data from the tracker.
  - `GET /api/dashboard`: returns occupancy and average dwell information excluding staff.
  - `GET /api/events/recent`: returns the most recent events.
  - `GET /api/auth/login`: basic authentication simulation.
- Persists events in a file-backed H2 database so data remains after restarts.
- Writes every received event as a JSON line to `event_log.jsonl` for audit and submission.

## Data Flow
1. Video frames are processed by the Python tracker.
2. Person IDs and line-crossing events are generated.
3. The tracker sends event payloads to `POST /api/events`.
4. The backend stores events and appends them to `event_log.jsonl`.
5. Dashboard clients request analytics from `/api/dashboard` and receive non-staff occupancy metrics.

## Event Schema
Each event payload includes:
- `personId`: string identifier for the tracked person.
- `eventType` / `event`: either `ENTRY` or `EXIT`.
- `timestamp`: UTC ISO-8601 timestamp.
- `cameraId`: optional camera identifier.
- `zoneId`: optional zone identifier.
- `dwellTimeSeconds`: optional duration for `EXIT` events.
- `isStaff` / `staffMember`: boolean to indicate staff members.

## Staff Exclusion
- Tracker configuration supports `STAFF_IDS` and `STAFF_PREFIX`.
- When staff are detected, the backend still stores the event, but analytics exclude staff counts and dwell time.

## Persistence
- Uses H2 in file-backed mode via `spring.datasource.url=jdbc:h2:file:./data/storedb;DB_CLOSE_ON_EXIT=FALSE;AUTO_SERVER=TRUE`.
- Keeps event history across application restarts.
- Uses `event_log.jsonl` for append-only event auditing.
