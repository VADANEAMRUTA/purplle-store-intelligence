# Implementation Choices

## Language and Framework
- `Python` was chosen for the tracker because of strong OpenCV and YOLOv8 support for video analytics and rapid prototyping.
- `Java Spring Boot` was chosen for the backend because it provides a structured REST API platform, built-in persistence support, and easy deployment.

## Detection and Tracking
- `YOLOv8` was selected for person detection because it provides reliable real-time object detection.
- A custom Euclidean distance tracker is used to maintain person identity across consecutive frames without requiring a heavier tracking library.

## Analytics and Persistence
- H2 database is used in file-backed mode for persistence with minimal setup, fulfilling challenge requirements without a separate database server.
- Event audit logging is implemented as JSONL so each event is preserved as a single newline-delimited JSON record.

## Staff Exclusion
- Staff members are identified by `STAFF_IDS` or `STAFF_PREFIX` configuration.
- This allows staff traffic to be recorded for traceability while excluding it from customer footfall and occupancy analytics.

## API Design
- Using a single `POST /api/events` ingestion endpoint keeps the tracker/backend contract simple.
- The backend separates staff-aware analytics using repository query filters so the dashboard always reflects customer-facing metrics.

## Deployment and Testing
- The Spring Boot backend is configured with CORS for local dashboard development.
- Debug and health endpoints are provided to verify the system is running.

## Database
Why H2 Database?

- Lightweight and embedded database
- No external database setup required
- Faster project evaluation for judges
- Easy local execution
- Suitable for prototype and hackathon environments