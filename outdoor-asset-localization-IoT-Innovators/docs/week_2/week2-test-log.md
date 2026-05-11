# Week 2 Test Log

## Overview
This document summarizes the main Week 2 software integration and dashboard tests completed for the **Outdoor Asset Localization** project.

The purpose of these tests was to verify that:
- received LoRa data can be stored in the backend/database
- the dashboard can display the latest asset location on a map
- multiple assets can be shown in the dashboard
- polling updates work correctly
- the system handles important edge cases such as missing GPS fix and stale data

---

## Week 2 Objective
Create the first complete software view of the system by saving and displaying location data.

---

## Test Setup

### Components Used
- **Sender node:** TTGO LoRa32 + NEO-6M GPS
- **Receiver node:** TTGO LoRa32
- **Python bridge script:** reads receiver Serial output and uploads records to Firebase
- **Backend:** Firebase Realtime Database
- **Dashboard:** HTML + JavaScript + Leaflet.js + OpenStreetMap
- **Browser runtime:** Live Server in VS Code

### Data Flow Validated
**GPS Sensor → Sender LoRa Board → Receiver LoRa Board → Python Serial Bridge → Firebase Realtime Database → Dashboard Map**

---

## Test 1 — Receiver to Firebase Data Ingestion

### Objective
Confirm that parsed receiver output is uploaded into Firebase successfully.

### Method
- The receiver node was connected to the laptop
- The Python bridge script `serial_to_firebase.py` was run
- The script read the parsed receiver packet from the COM port
- The script updated:
  - `assets/<deviceId>/latest`
  - `assets/<deviceId>/history`

### Result
**Successful**

### Observation
Firebase updated correctly with real asset data received from the live LoRa receiver output.

### Validation
The backend now stores received location records, satisfying the first main Week 2 backend requirement.

---

## Test 2 — Dashboard v1 Single-Asset Display

### Objective
Confirm that the dashboard can load and display the latest asset location from Firebase.

### Method
- `dashboard_v1.html` was opened using Live Server
- The dashboard fetched data from Firebase
- The latest coordinates of `ASSET-01` were loaded
- A map marker and information panel were displayed

### Result
**Successful**

### Observation
The map loaded correctly and displayed the most recent location of the asset, along with:
- device ID
- GPS fix
- latitude
- longitude
- timestamp
- satellites
- HDOP
- RSSI
- receivedAt

### Validation
This confirms that Dashboard v1 can display the latest current position of an asset on a map.

---

## Test 3 — Dashboard Polling / Auto Refresh

### Objective
Confirm that the dashboard updates automatically when new data is stored in Firebase.

### Method
- Polling was added using:
  `setInterval(loadAllAssets, 5000);`
- The sender continued transmitting live data
- The Python bridge continued uploading updates to Firebase
- The dashboard was observed over time

### Result
**Successful**

### Observation
The dashboard updated automatically every 5 seconds:
- panel values refreshed
- latest timestamp changed
- marker position updated when coordinates changed

### Validation
This confirms the first version of live update behavior using polling.

---

## Test 4 — Multi-Asset Support

### Objective
Confirm that the dashboard can display multiple assets.

### Method
- Real asset:
  - `ASSET-01`
- Simulated assets added manually to Firebase:
  - `ASSET-02`
  - `ASSET-03`
- Dashboard logic was updated to fetch `/assets.json`
- A marker was created for each asset

### Result
**Successful**

### Observation
The dashboard displayed multiple asset markers and allowed switching between assets using:
- marker click
- dropdown asset selector

### Validation
This confirms basic multi-asset support, even when only one real hardware sender is available.

---

## Test 5 — Edge Case: Missing GPS Fix

### Objective
Confirm that the dashboard handles an asset with no valid GPS fix.

### Method
- `ASSET-03` was configured in Firebase with:
  - `fix = 0`

### Result
**Successful**

### Observation
When `ASSET-03` was selected:
- the dashboard displayed **No GPS Fix**
- the status badge reflected the invalid GPS state correctly
- asset data remained visible without crashing the interface

### Validation
The dashboard correctly handles the missing GPS fix edge case.

---

## Test 6 — Edge Case: Stale / Delayed Data

### Objective
Confirm that the dashboard detects delayed data.

### Method
- `ASSET-02/latest/receivedAt` was manually changed to an older timestamp in Firebase
- The dashboard was refreshed / allowed to poll again

### Result
**Successful**

### Observation
The dashboard displayed:
- **Stale Data**
- warning-style status badge
- note indicating delayed or outdated updates

### Validation
The dashboard correctly detects delayed packet/backend update situations.

---

## Test 7 — Edge Case: Invalid Payload Handling

### Objective
Confirm that invalid or malformed packet blocks do not corrupt backend data.

### Method
- The Python ingestion script only uploads records when parsing succeeds
- If parsing fails or `deviceId` is missing, the record is ignored

### Result
**Successful**

### Observation
Invalid or incomplete packet blocks are skipped and are not uploaded to Firebase.

### Validation
The backend is protected from malformed payloads at the ingestion stage.

---

## Dashboard Usability Improvements Completed
The following usability improvements were added in Week 2:
- asset selector dropdown
- multiple map markers
- status badges:
  - Live
  - No GPS Fix
  - Stale Data
- last refresh field
- asset information panel with clear labels
- click marker to show asset details

---

## Week 2 Deliverables Status

### Deliverable 1
**The backend/database keeps track of the location records that have been received.**  
**Status:** Completed

### Deliverable 2
**Dashboard v1 shows the current position of assets on a map.**  
**Status:** Completed

### Deliverable 3
**A successful end-to-end demo from the sensor to the transmission path to the backend to the dashboard.**  
**Status:** Completed

### Deliverable 4
**A short test log of edge cases and fixes.**  
**Status:** Completed

---

## Evidence Collected
Recommended evidence files for Week 2:
- `evidence_week_2/firebase-live-data_history.png`
- `evidence_week_2/firebase-live-data_latest.png`
- `evidence/dashboard-v1-live.png`
- `evidence/dashboard-multi-asset.png`
- `evidence/dashboard-no-fix.png`
- `evidence/dashboard-stale-data.png`
- `evidence/python-bridge-terminal.png`

---

## Week 2 Conclusion
Week 2 successfully completed the first full software view of the project.

The system now supports:
- live backend data ingestion
- latest location storage
- dashboard map visualization
- polling-based updates
- multi-asset view
- edge-case handling for no-fix and stale-data situations

The project is now ready to move into Week 3, where the main focus will be:
- historical movement trail
- geofence feature
- longer consistency tests
- further technical documentation