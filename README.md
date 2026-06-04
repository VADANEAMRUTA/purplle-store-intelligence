# Purplle Store Intelligence

This repository contains a retail store customer analytics system with two primary subsystems:
- `python-tracker`: video analytics for person detection, tracking, and store entry/exit event generation.
- `spring-boot-api`: Spring Boot backend that receives events, stores them in H2, writes JSONL audit logs, and serves dashboard analytics.

## Folder Structure
- `dashboard/`: front-end dashboard files.
- `python-tracker/`: tracker pipeline, detector, and event publisher.
- `spring-boot-api/`: Java REST API, persistence, and analytics.
- `event_log.jsonl`: append-only audit log of received events.

## Setup
1. Start the backend:
   - Open `spring-boot-api` in a Java IDE or run `mvn spring-boot:run` from `spring-boot-api`.
2. Start the tracker:
   - Install Python dependencies from `python-tracker/requirements.txt`.
   - Configure staff exclusion using `STAFF_IDS` and `STAFF_PREFIX` if needed.
   - Run `python main.py` or `python app.py` from `python-tracker`.
3. Open the dashboard in the browser and point it to the backend API.

## Notes
- Staff members are configured using `STAFF_IDS` and/or `STAFF_PREFIX` and are excluded from occupancy analytics.
- The backend persists events across restarts using file-backed H2 and produces an event audit log at `event_log.jsonl`.

## Database
Database: H2 Embedded Database

The application uses H2 for simplicity and quick setup. No separate database installation is required.


## Demo Video

Demo Link:
https://drive.google.com/file/d/1D2qjdOULWSz3nPDkgmT-lX_IxCcRCvXe/view?usp=drivesdk
