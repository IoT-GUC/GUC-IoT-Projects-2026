# Outdoor Asset Localization

## Project Overview

This project implements an IoT-based outdoor asset localization system using a **NEO-6M GPS module** and **LILYGO TTGO LoRa32 boards**.

The system tracks outdoor assets by collecting live GPS coordinates from a sender node, transmitting them wirelessly using **LoRa**, forwarding the received data through **WiFi/MQTT**, storing it in **Firebase Realtime Database**, and displaying the latest asset location on a web dashboard.

This project is developed as an academic IoT prototype for **NETW1010: Internet of Things**.

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

## Current System Flow

```text
NEO-6M GPS Module
        ↓
TTGO LoRa32 Sender
        ↓
LoRa Wireless Communication
        ↓
TTGO LoRa32 Receiver / Gateway
        ↓
WiFi + MQTT
        ↓
MQTT to Firebase Bridge
        ↓
Firebase Realtime Database
        ↓
Web Dashboard
```

---

## System Architecture

### 1. Sensing Layer

The **NEO-6M GPS module** collects live outdoor location data and sends GPS information to the ESP32 sender board through UART.

### 2. Sender Node

The **TTGO LoRa32 sender** reads GPS data, checks the GPS fix status, builds a structured payload, and transmits it through LoRa.

A **No-OLED sender version** was added to reduce unnecessary power consumption. The OLED screen is not required for normal tracking operation, so the sender now depends on Serial Monitor only for debugging.

### 3. LoRa Communication Layer

The sender and receiver communicate using direct **LoRa communication**. LoRa is used because it is suitable for long-range, low-power IoT communication.

### 4. Receiver / Gateway Layer

The **TTGO LoRa32 receiver** receives LoRa packets from the sender.

In Week 2, the receiver output was read through the USB COM port using a Python serial bridge.

In the updated Week 3 implementation, the receiver acts as a **LoRa-to-WiFi/MQTT gateway**. It receives LoRa packets, parses them, converts them into JSON, and publishes them to an MQTT broker over WiFi.

### 5. Backend Layer

The backend uses **Firebase Realtime Database** to store:

- latest asset location
- historical location records
- GPS fix status
- RSSI
- satellite count
- timestamp
- gateway information

### 6. Dashboard Layer

The dashboard uses **HTML, CSS, JavaScript, Leaflet.js, and OpenStreetMap** to display the asset location on a map.

The dashboard reads from Firebase and shows:

- current asset location
- GPS fix status
- latitude and longitude
- UTC timestamp
- RSSI
- satellites
- HDOP
- received time
- live/stale status

---

## Hardware Used

- NEO-6M GPS module
- LILYGO TTGO LoRa32 board as sender
- LILYGO TTGO LoRa32 board as receiver/gateway
- Female-to-female jumper wires
- USB data cables
- Laptop for programming, testing, and dashboard viewing

---

## Technologies Used

### Embedded / IoT

- ESP32
- TTGO LoRa32
- NEO-6M GPS
- LoRa communication
- WiFi
- MQTT

### Arduino Libraries

- TinyGPSPlus
- LoRa
- PubSubClient
- ArduinoJson

### Backend

- Python 3
- requests
- paho-mqtt
- Firebase Realtime Database

### Frontend

- HTML
- CSS
- JavaScript
- Leaflet.js
- OpenStreetMap

---

## Repository Structure

```text
outdoor-asset-localization-IoT-Innovators/
│
├── README.md
│
├── firmware/
│   ├── Sender_v1.0/
│   │   └── Sender_v1.0.ino
│   │
│   ├── Sender_NoOLED_v1.0/
│   │   └── Sender_NoOLED_v1.0.ino
│   │
│   ├── Receiver_v1.0/
│   │   └── Receiver_v1.0.ino
│   │
│   └── Receiver_MQTT_v1.0/
│       └── Receiver_MQTT_v1.0.ino
│
├── backend/
│   ├── serial_to_firebase.py
│   ├── mqtt_to_firebase.py
│   └── requirements.txt
│
├── dashboard/
│   └── dashboard_v1.html
│
├── docs/
│   ├── week_1/
│   │   ├── backend-schema.md
│   │   ├── payload-format.md
│   │   ├── week-1-test-log.md
│   │   └── wiring-reference.md
│   │
│   ├── week_2/
│   │   └── week2-test-log.md
│   │
│   └── week_3/
│       └── mqtt-integration.md
│
├── evidence/
│   ├── week_1/
│   │   ├── firebase-initial-schema.png
│   │   ├── Receiver_Serial_Monitor_Output.png
│   │   └── Sender_Serial_Monitor_Output.png
│   │
│   ├── week_2/
│   │   ├── dashboard-multi-asset.png
│   │   ├── dashboard-no-fix.png
│   │   ├── dashboard-stale-data.png
│   │   ├── dashboard-v1-live.png
│   │   ├── firebase-live-data_history.png
│   │   ├── firebase-live-data_latest.png
│   │   └── python-bridge-terminal.png
│   │
│   └── week_3/
│       ├── mqtt-receiver-serial.png
│       ├── mqtt-to-firebase-bridge.png
│       ├── firebase-latest-mqtt.png
│       ├── firebase-history-mqtt.png
│       └── dashboard-mqtt-live.png
│
├── presentation/
│   └── IoT_Innovators_Presentation.pdf
│
├── references/
│   └── references.md
│
└── diagrams/
    └── system-architecture.png
```

---

## Firmware Files

### Sender v1.0

```text
firmware/Sender_v1.0/Sender_v1.0.ino
```

This is the original sender firmware. It reads GPS data, sends LoRa packets, and uses the onboard OLED for local display.

### Sender No-OLED v1.0

```text
firmware/Sender_NoOLED_v1.0/Sender_NoOLED_v1.0.ino
```

This is the updated low-power sender version.

It performs the same core function as the original sender:

```text
GPS → TTGO Sender → LoRa transmission
```

However, the OLED code was removed to reduce unnecessary power usage.

The sender still prints debug information to Serial Monitor during testing.

### Receiver v1.0

```text
firmware/Receiver_v1.0/Receiver_v1.0.ino
```

This is the Week 2 receiver firmware. It receives LoRa packets and prints the parsed output to Serial Monitor.

Receiver validation in Week 2 was completed using Serial Monitor output instead of OLED because OLED initialization on the receiver caused watchdog reset issues.

### Receiver MQTT v1.0

```text
firmware/Receiver_MQTT_v1.0/Receiver_MQTT_v1.0.ino
```

This is the updated Week 3 receiver/gateway firmware.

It performs the following:

1. Connects to WiFi.
2. Connects to an MQTT broker.
3. Initializes LoRa.
4. Receives LoRa packets from the sender.
5. Parses the CSV payload.
6. Converts the payload to JSON.
7. Publishes the JSON message to MQTT.
8. Prints debug output to Serial Monitor.

---

## Payload Format

The sender transmits the following CSV payload through LoRa:

```text
deviceID,fix,latitude,longitude,timestamp_utc,satellites,hdop,uptime
```

Example:

```text
ASSET-01,1,29.992221,31.555294,2026-05-12T17:54:49Z,5,2.0,2523
```

### Payload Fields

| Field | Description |
|---|---|
| deviceID | Unique asset/device identifier |
| fix | GPS fix status, where 1 means valid fix and 0 means invalid fix |
| latitude | GPS latitude |
| longitude | GPS longitude |
| timestamp_utc | UTC timestamp from GPS |
| satellites | Number of satellites detected |
| hdop | Horizontal dilution of precision |
| uptime | Device uptime in seconds |

---

## MQTT Integration

### MQTT Purpose

MQTT was added to improve the Week 2 architecture by removing the dependency on the receiver USB COM port for sending data to the backend.

In Week 2, the receiver printed data to Serial Monitor, and a Python script read that data from the COM port.

In the updated architecture, the receiver publishes data directly over WiFi using MQTT.

---

## Correct MQTT Architecture

```text
Sender = GPS + LoRa only
Receiver = LoRa + WiFi + MQTT gateway
```

The sender still sends data using LoRa.  
The receiver receives LoRa data and forwards it using WiFi/MQTT.

Correct explanation:

```text
The receiver receives data through LoRa and forwards it through WiFi using MQTT.
```

Incorrect explanation:

```text
LoRa sends data through WiFi.
```

---

## MQTT Broker

The current test implementation uses the public HiveMQ broker:

```text
broker.hivemq.com
```

Port:

```text
1883
```

This is used for academic testing. A production system should use a private or authenticated MQTT broker.

---

## MQTT Topics

### Main Asset Topic

```text
iot-innovators/assets/all
```

All asset location messages are published to this topic.

### Per-Asset Topic

```text
iot-innovators/assets/<deviceID>/location
```

Example:

```text
iot-innovators/assets/ASSET-01/location
```

### Gateway Status Topic

```text
iot-innovators/gateway/status
```

Used to publish receiver gateway status.

### Gateway Debug Topic

```text
iot-innovators/gateway/debug
```

Used to publish invalid packet/debug messages.

---

## MQTT JSON Payload

The receiver converts the LoRa CSV payload into JSON before publishing it to MQTT.

Example:

```json
{
  "deviceID": "ASSET-01",
  "fix": 1,
  "latitude": 29.99222,
  "longitude": 31.55529,
  "timestamp_utc": "2026-05-12T17:54:49Z",
  "satellites": 5,
  "hdop": 2.0,
  "uptime": 2523,
  "rssi": -31,
  "gateway": "receiver01",
  "packet_count": 473,
  "raw_payload": "ASSET-01,1,29.992221,31.555294,2026-05-12T17:54:49Z,5,2.0,2523"
}
```

---

## Backend Files

### Serial to Firebase Bridge

```text
backend/serial_to_firebase.py
```

This was used in Week 2.

It reads receiver output from the COM port and uploads the parsed location data to Firebase.

This file is kept as a legacy validation path.

### MQTT to Firebase Bridge

```text
backend/mqtt_to_firebase.py
```

This is the updated backend bridge.

It subscribes to:

```text
iot-innovators/assets/all
```

When an MQTT message is received, it:

1. Parses the JSON payload.
2. Validates required fields.
3. Normalizes the data.
4. Adds dashboard-compatible field aliases.
5. Uploads the latest asset data to Firebase.
6. Appends the record to Firebase history.

---

## Firebase Database Structure

The backend stores data under:

```text
assets/<deviceID>/latest
assets/<deviceID>/history
```

Example:

```text
assets
 └── ASSET-01
      ├── latest
      │    ├── deviceID
      │    ├── fix
      │    ├── latitude
      │    ├── longitude
      │    ├── timestamp_utc
      │    ├── satellites
      │    ├── hdop
      │    ├── uptime
      │    ├── rssi
      │    ├── gateway
      │    ├── source
      │    └── updated_at
      │
      └── history
           ├── record1
           ├── record2
           └── record3
```

The MQTT bridge also stores dashboard-compatible aliases such as:

```text
device_id
timestamp
received_at
last_updated
lat
lng
gps_fix
```

This allows the existing dashboard to work without major changes.

---

## Dashboard

### File

```text
dashboard/dashboard_v1.html
```

The dashboard displays the latest asset data from Firebase.

### Dashboard Features

- Leaflet.js map
- OpenStreetMap tiles
- asset marker on map
- asset selector
- live/stale status
- device ID
- GPS fix status
- latitude
- longitude
- UTC timestamp
- satellites
- HDOP
- RSSI
- received time
- automatic refresh

---

## Installation and Setup

### 1. Arduino IDE Setup

Install the ESP32 board package in Arduino IDE.

Use the board:

```text
TTGO-LoRa32-OLED
```

or if unavailable:

```text
ESP32 Dev Module
```

### 2. Arduino Libraries

Install the following libraries from Arduino Library Manager:

```text
TinyGPSPlus
LoRa
PubSubClient
ArduinoJson
```

`WiFi.h` is included with the ESP32 board package.

OLED libraries are not required for the No-OLED sender or MQTT receiver.

---

## Uploading the Sender

Open:

```text
firmware/Sender_NoOLED_v1.0/Sender_NoOLED_v1.0.ino
```

Check:

```cpp
#define GPS_RX_PIN 34
#define GPS_TX_PIN -1
#define LORA_BAND 868E6
const char* DEVICE_ID = "ASSET-01";
```

Upload the code to the sender TTGO board.

Open Serial Monitor at:

```text
115200 baud
```

Expected output:

```text
GPS + LoRa Sender starting...
Mode: No OLED / Low-power sender
LoRa init OK
Waiting for GPS data...
LoRa Packet Sent
```

---

## Uploading the Receiver MQTT Gateway

Open:

```text
firmware/Receiver_MQTT_v1.0/Receiver_MQTT_v1.0.ino
```

Before uploading, update WiFi credentials:

```cpp
const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
```

Check that the LoRa band matches the sender:

```cpp
#define LORA_BAND 868E6
```

Upload the code to the receiver TTGO board.

Open Serial Monitor at:

```text
115200 baud
```

Expected output:

```text
IoT Innovators LoRa MQTT Receiver
WiFi connected successfully
MQTT connected
LoRa receiver initialized successfully
Waiting for LoRa packets...
```

When packets arrive:

```text
LoRa Packet Received
Payload parsed successfully
MQTT publish successful
```

---

## Running the Backend

Go to the backend folder:

```bash
cd backend
```

Create and activate a virtual environment if needed:

```bash
python -m venv venv
```

Windows PowerShell:

```bash
.\\venv\\Scripts\\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the MQTT to Firebase bridge:

```bash
python mqtt_to_firebase.py
```

Expected output:

```text
MQTT Message Received
Normalized record:
Uploaded to Firebase successfully.
Latest path: assets/ASSET-01/latest
History path: assets/ASSET-01/history
```

---

## Python Requirements

The backend requirements are:

```text
pyserial
requests
paho-mqtt
```

`pyserial` is kept for the Week 2 serial bridge.  
`paho-mqtt` is used for the Week 3 MQTT bridge.  
`requests` is used to upload data to Firebase.

---

## Opening the Dashboard

Open the dashboard using VS Code Live Server:

```text
dashboard/dashboard_v1.html
```

The dashboard reads from Firebase, so it works with both:

```text
Week 2: Serial Bridge → Firebase
Week 3: MQTT Bridge → Firebase
```

For the updated MQTT version, the full flow is:

```text
Sender_NoOLED → LoRa → Receiver_MQTT → MQTT → mqtt_to_firebase.py → Firebase → Dashboard
```

---

## Week 1 Progress

Week 1 focused on stable embedded communication.

### Completed

- Sender firmware created.
- Receiver firmware created.
- GPS module connected to sender.
- LoRa communication tested.
- Payload format documented.
- Wiring reference documented.
- Outdoor GPS-to-LoRa tests performed.
- Initial Firebase backend schema prepared.
- Evidence screenshots collected.

### Week 1 Evidence

```text
evidence/week_1/
```

---

## Week 2 Progress

Week 2 focused on creating the first end-to-end software path.

### Completed

- Receiver output connected to Firebase using Python serial bridge.
- Firebase stores latest asset location.
- Firebase stores location history.
- Dashboard v1 created.
- Dashboard displays asset location on map.
- Dashboard supports asset selection.
- Dashboard displays coordinates and status fields.
- Edge cases handled:
  - missing GPS fix
  - delayed/stale packets
  - invalid payloads
  - multiple asset IDs

### Week 2 Evidence

```text
evidence/week_2/
```

---

## Week 3 Progress

Week 3 improves the architecture based on feedback.

### Completed

- Added No-OLED sender firmware to reduce unnecessary power usage.
- Added MQTT receiver/gateway firmware.
- Receiver now connects to WiFi.
- Receiver now publishes received LoRa packets to MQTT.
- Added MQTT to Firebase bridge.
- Firebase now receives data from MQTT.
- Existing dashboard works with MQTT-updated Firebase data.
- UTC timestamp, device ID, and received time are visible on dashboard.
- Evidence screenshots collected.

### Week 3 Evidence

```text
evidence/week_3/
```

Recommended evidence files:

```text
mqtt-receiver-serial.png
mqtt-to-firebase-bridge.png
firebase-latest-mqtt.png
firebase-history-mqtt.png
dashboard-mqtt-live.png
```

---

## Design Decisions

### 1. Sender Kept as GPS + LoRa Only

The sender is attached to the moving asset, so it should remain simple and power-efficient.

Adding WiFi/MQTT to the sender would increase power consumption and reduce the benefit of using LoRa.

Therefore:

```text
Sender = GPS + LoRa only
```

### 2. Receiver Upgraded into Gateway

The receiver is less power-sensitive and can act as the internet gateway.

Therefore:

```text
Receiver = LoRa + WiFi + MQTT
```

### 3. OLED Disabled in Updated Sender

The OLED display is useful for debugging but not required for final operation.

A No-OLED sender version was added to reduce power consumption.

### 4. Firebase Kept as Backend

The dashboard was already working with Firebase, so the MQTT upgrade was integrated by adding an MQTT-to-Firebase bridge instead of rebuilding the dashboard from scratch.

---

## Known Limitations

- GPS fix may be slow or unavailable indoors.
- MQTT currently uses a public broker for testing.
- Firebase is configured for academic prototype use.
- Dashboard uses polling rather than direct real-time MQTT subscription.
- Power consumption has not yet been fully measured.
- TTN/LoRaWAN integration is not part of the current core implementation.

---

## Future Improvements

- Add geofence warning.
- Add movement history trail on the map.
- Measure sender power consumption with OLED disabled.
- Add private/authenticated MQTT broker.
- Add stronger Firebase security rules.
- Host the dashboard online.
- Add battery monitoring.
- Add data export for testing and analysis.
- Add optional TTN/LoRaWAN integration if gateway access is available.

---

## Academic Prototype Notice

This repository is an academic IoT prototype. It is intended for demonstration, experimentation, and learning purposes.

A production-ready outdoor asset localization system would require stronger security, enclosure design, power optimization, authenticated cloud communication, and extended field testing.
