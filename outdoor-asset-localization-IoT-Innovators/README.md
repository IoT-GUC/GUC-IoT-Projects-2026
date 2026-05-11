# Outdoor Asset Localization

## Project Overview

This project implements an IoT-based outdoor asset localization system using a **NEO-6M GPS module** and **two LILYGO TTGO LoRa32 boards**.

The goal is to track outdoor assets such as campus shuttles, construction equipment, or delivery vehicles by acquiring live GPS coordinates from a sender node, transmitting them wirelessly using **LoRa**, storing the received data in **Firebase Realtime Database**, and displaying the latest asset locations on a web dashboard.

This project is built as a low-cost academic prototype for **NETW1010: Internet of Things**.

---

## Team Information

**Team Name:** IoT Innovators  
**Project Name:** Outdoor Asset Localization  

### Team Members

- Adam Amr
- Kareem Emad
- George Ehab
- Farah Khaled
- Rahma Mohamed

---

## System Flow

```text
NEO-6M GPS Module
        ↓
TTGO LoRa32 Sender
        ↓
LoRa Wireless Communication
        ↓
TTGO LoRa32 Receiver
        ↓
Python Serial-to-Firebase Bridge
        ↓
Firebase Realtime Database
        ↓
Web Dashboard with Map
```

---

## Full System Architecture

### 1. Sensing Layer

The **NEO-6M GPS module** collects outdoor location data and sends NMEA GPS sentences to the ESP32 through UART.

### 2. Edge Processing Layer

The **TTGO LoRa32 sender board** reads GPS data, checks whether a valid GPS fix exists, extracts location information, formats it into a structured payload, and transmits it over LoRa.

### 3. Wireless Communication Layer

The sender and receiver communicate using direct **LoRa communication**. This is used as the core communication method for testing and demonstration.

### 4. Receiver / Ingestion Layer

The **TTGO LoRa32 receiver board** receives LoRa packets, parses the payload, and prints structured readings to the Serial Monitor.

A Python bridge script reads this serial output and sends valid records to Firebase.

### 5. Backend Layer

**Firebase Realtime Database** stores the latest location for each asset and keeps a history of received location records.

### 6. User Interface Layer

A web dashboard displays asset locations on a map using **Leaflet.js** and **OpenStreetMap** tiles. The dashboard supports live refresh, asset selection, multiple markers, status indicators, coordinates, timestamps, and basic error handling.

---

## Hardware Used

- 1 × NEO-6M GPS module
- 2 × LILYGO TTGO LoRa32 boards
  - one board as sender
  - one board as receiver
- Female-to-female jumper wires
- USB data cables
- Laptop for Arduino programming, testing, dashboard viewing, and serial bridge execution

---

## Software Used

- Arduino IDE
- ESP32 board package
- TinyGPSPlus Arduino library
- LoRa Arduino library
- Python 3
- PySerial
- Requests
- Firebase Realtime Database
- HTML, CSS, and JavaScript
- Leaflet.js
- OpenStreetMap tiles

---

## Repository Structure

```text
Outdoor-Asset-Localization/
│
├── firmware/
│   ├── Sender_v1.0/
│   │   └── Sender_v1.0.ino
│   │
│   └── Receiver_v1.0/
│       └── Receiver_v1.0.ino
│
├── docs_week_1/
│   ├── backend-schema.md
│   ├── payload-format.md
│   ├── week-1-test-log.md
│   └── wiring-reference.md
│
├── docs_week_2/
│   └── week2-test-log.md
│
├── evidence_week_1/
│   ├── firebase-initial-schema.png
│   ├── Receiver_Serial_Monitor_Output.png
│   └── Sender_Serial_Monitor_Output.png
│
├── evidence_week_2/
│   ├── dashboard-multi-asset.png
│   ├── dashboard-no-fix.png
│   ├── dashboard-stale-data.png
│   ├── dashboard-v1-live.png
│   ├── firebase-live-data_history.png
│   ├── firebase-live-data_latest.png
│   └── python-bridge-terminal.png
│
├── dashboard_v1.html
├── serial_to_firebase.py
├── requirements.txt
└── README.md
```

---

## Week 1 Status

### Objective

Make the embedded system stable and document the hardware setup for demonstration.

### Week 1 Deliverables Completed

- Stable sender firmware created.
- Stable receiver firmware created.
- GPS module connected to TTGO LoRa32 sender.
- LoRa sender-to-receiver communication tested.
- Payload format documented.
- Wiring reference documented.
- Outdoor GPS-to-LoRa testing performed.
- Serial Monitor screenshots collected.
- Firebase selected as backend.
- Initial backend schema created.

### Week 1 Files

```text
firmware/Sender_v1.0/Sender_v1.0.ino
firmware/Receiver_v1.0/Receiver_v1.0.ino
docs_week_1/wiring-reference.md
docs_week_1/payload-format.md
docs_week_1/week-1-test-log.md
docs_week_1/backend-schema.md
evidence_week_1/
```

---

## Week 2 Status

### Objective

Create the first complete software view of the system by storing and displaying location data.

### Week 2 Deliverables Completed

- Python serial-to-Firebase bridge implemented.
- Receiver output connected to backend storage path.
- Firebase stores latest asset location.
- Firebase stores historical received records.
- Dashboard v1 created using Leaflet.js and OpenStreetMap.
- Dashboard displays current asset position on a map.
- Dashboard supports multiple assets.
- Dashboard supports asset selection.
- Dashboard displays latitude, longitude, timestamp, RSSI, satellites, and GPS fix status.
- Dashboard refreshes automatically.
- Edge cases tested:
  - missing GPS fix
  - delayed or stale data
  - invalid payloads
  - multiple asset IDs

### Week 2 Files

```text
serial_to_firebase.py
dashboard_v1.html
docs_week_2/week2-test-log.md
evidence_week_2/
```

---

## Firmware Files

### Sender Firmware

```text
firmware/Sender_v1.0/Sender_v1.0.ino
```

The sender node:

- reads live GPS data from the NEO-6M module
- checks whether a valid GPS fix exists
- extracts coordinates and GPS status values
- builds a structured LoRa payload
- transmits the payload periodically over LoRa

### Receiver Firmware

```text
firmware/Receiver_v1.0/Receiver_v1.0.ino
```

The receiver node:

- listens for incoming LoRa packets
- reads received payloads
- parses each field
- prints structured output to the Serial Monitor
- displays RSSI for link quality monitoring

---

## Wiring Reference

### GPS to TTGO LoRa32 Sender

| GPS Pin | TTGO LoRa32 Sender Pin | Purpose |
|---|---|---|
| VCC | 5V | Powers the GPS module |
| GND | GND | Common ground |
| TXD | GPIO34 | Sends GPS serial data to ESP32 |
| RXD | Not connected | Not required in current implementation |

### Wiring Notes

- The GPS module sends serial data through **TXD**.
- The ESP32 listens on **GPIO34**.
- GPS RXD is not required because the current implementation only reads from the GPS module.
- The GPS patch antenna should face upward toward the sky during outdoor testing.
- Both TTGO boards are powered through USB during development.

---

## Payload Format

### Current Payload Structure

```text
deviceID,fix,latitude,longitude,timestamp_utc,satellites,hdop,uptime
```

### Example Payload

```text
asset001,1,30.044420,31.235712,12:35:42,6,1.20,15430
```

### Payload Fields

| Field | Description |
|---|---|
| deviceID | Unique asset/device identifier |
| fix | GPS fix status, where 1 means valid and 0 means invalid |
| latitude | GPS latitude |
| longitude | GPS longitude |
| timestamp_utc | UTC time from GPS |
| satellites | Number of satellites detected |
| hdop | Horizontal dilution of precision |
| uptime | Device uptime in milliseconds |

---

## Backend

The project uses **Firebase Realtime Database** as the backend for the current prototype.

### Database Purpose

Firebase stores:

- latest location per asset
- historical location records
- GPS fix status
- RSSI value
- satellite count
- timestamp
- update time

### Example Firebase Structure

```json
{
  "assets": {
    "asset001": {
      "latest": {
        "deviceID": "asset001",
        "fix": 1,
        "latitude": 30.04442,
        "longitude": 31.235712,
        "timestamp_utc": "12:35:42",
        "satellites": 6,
        "hdop": 1.2,
        "uptime": 15430,
        "rssi": -72,
        "updated_at": "2026-05-06T12:35:42Z"
      },
      "history": {
        "record_id": {
          "deviceID": "asset001",
          "fix": 1,
          "latitude": 30.04442,
          "longitude": 31.235712,
          "timestamp_utc": "12:35:42",
          "satellites": 6,
          "hdop": 1.2,
          "uptime": 15430,
          "rssi": -72,
          "updated_at": "2026-05-06T12:35:42Z"
        }
      }
    }
  }
}
```

### Firebase Prototype Note

Firebase Realtime Database is currently used for academic demonstration. In a production version, database access should be protected using authentication and stricter Firebase security rules.

---

## Python Serial-to-Firebase Bridge

### File

```text
serial_to_firebase.py
```

### Purpose

The Python bridge reads structured serial output from the TTGO LoRa32 receiver and uploads valid readings to Firebase.

### What It Does

- Opens the serial port connected to the receiver.
- Reads incoming LoRa packet lines.
- Parses payload fields.
- Extracts RSSI.
- Validates GPS fix and coordinate data.
- Sends latest asset data to Firebase.
- Appends records to asset history.

### Important Configuration

Inside `serial_to_firebase.py`, update the following values if needed:

```python
SERIAL_PORT = "COM3"
BAUD_RATE = 115200
FIREBASE_BASE_URL = "https://outdoor-asset-localization-default-rtdb.firebaseio.com"
```

### COM Port Note

The serial port may be different depending on the laptop. For example:

```text
COM3
COM4
COM5
```

Check the correct port from Arduino IDE under:

```text
Tools → Port
```

---

## Dashboard

### File

```text
dashboard_v1.html
```

### Dashboard Features

The dashboard currently supports:

- live map view
- Leaflet.js map integration
- OpenStreetMap tiles
- latest asset marker
- multiple asset markers
- asset selection dropdown
- coordinate panel
- GPS fix status
- RSSI display
- satellite count display
- last update timestamp
- automatic refresh every 5 seconds
- stale data warning
- no-fix handling

### How to Open the Dashboard

Open the file directly in a browser:

```text
dashboard_v1.html
```

Or use VS Code Live Server if available.

---

## Installation and Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Outdoor-Asset-Localization
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Upload Sender Firmware

Open Arduino IDE and upload:

```text
firmware/Sender_v1.0/Sender_v1.0.ino
```

to the TTGO LoRa32 sender board.

### 4. Upload Receiver Firmware

Open Arduino IDE and upload:

```text
firmware/Receiver_v1.0/Receiver_v1.0.ino
```

to the TTGO LoRa32 receiver board.

### 5. Connect the GPS Module

Connect the NEO-6M GPS module to the sender board using the wiring reference in:

```text
docs_week_1/wiring-reference.md
```

### 6. Run the Python Bridge

Make sure the receiver board is connected to the laptop, then run:

```bash
python serial_to_firebase.py
```

If the COM port is different, update it inside the script before running.

### 7. Open the Dashboard

Open:

```text
dashboard_v1.html
```

in a browser.

---

## Testing Summary

### Week 1 Testing

Week 1 focused on validating:

- GPS module output
- sender firmware stability
- LoRa packet transmission
- receiver parsing
- RSSI display
- payload format correctness

Evidence is available in:

```text
evidence_week_1/
```

### Week 2 Testing

Week 2 focused on validating:

- serial-to-Firebase bridge
- Firebase latest records
- Firebase history records
- dashboard map display
- multi-asset support
- missing GPS fix handling
- stale data handling
- invalid payload handling

Evidence is available in:

```text
evidence_week_2/
```

Test log:

```text
docs_week_2/week2-test-log.md
```

---

## Current Completion Status

| Project Area | Status |
|---|---|
| GPS reading | Completed |
| LoRa sender firmware | Completed |
| LoRa receiver firmware | Completed |
| Payload format | Completed |
| Wiring documentation | Completed |
| Firebase backend selection | Completed |
| Firebase schema | Completed |
| Serial-to-Firebase bridge | Completed |
| Dashboard v1 | Completed |
| Multi-asset support | Completed |
| Edge-case handling | Completed |
| History trail on map | Planned for Week 3 |
| Geofence warning | Planned for Week 3 |
| Longer outdoor testing | Planned for Week 3 |
| Final documentation and presentation | Planned for Week 4 |

---

## Planned Week 3 Work

The next phase will focus on adding the main project features beyond basic live tracking.

### Planned Tasks

- Display historical movement trail on the dashboard map.
- Implement a simple geofence.
- Show warning when an asset leaves the allowed area.
- Run longer outdoor LoRa transmission tests.
- Improve technical documentation.
- Add more complete architecture and data-flow diagrams.
- Continue improving dashboard UI.

---

## Known Limitations

- GPS fix may be slow or unavailable indoors.
- Firebase is currently configured for prototype/demo use.
- The dashboard currently uses polling instead of full real-time listeners.
- Power consumption measurement is not yet implemented.
- TTN/LoRaWAN support is optional and not part of the current core implementation.
- Current dashboard is a local HTML prototype, not a hosted web application.

---

## Future Improvements

- Add history trail visualization.
- Add geofence warning.
- Add power consumption measurements.
- Add better authentication and Firebase security rules.
- Add hosted dashboard deployment.
- Add optional TTN/LoRaWAN support.
- Add device battery status if hardware support is added.
- Add exportable logs for testing and analysis.

---

## Academic Prototype Notice

This repository is an academic IoT prototype. It is intended for demonstration, experimentation, and learning purposes. A production-ready asset localization system would require stronger security, reliable enclosure design, power optimization, authentication, and field validation.
