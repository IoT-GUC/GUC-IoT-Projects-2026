# Outdoor Asset Localization

---
## Project Overview

This project implements an IoT-based outdoor asset localization system using a **NEO-6M GPS module** and **LILYGO TTGO LoRa32 boards**.

The system tracks outdoor assets by collecting live GPS coordinates from a sender node, transmitting them wirelessly using **LoRa**, forwarding the received data through **WiFi/MQTT**, storing it in **Firebase Realtime Database**, and displaying the asset location on web dashboards.

This repository acts as the **final project report** for the Outdoor Asset Localization project. It documents the system architecture, hardware setup, firmware, backend, dashboards, Firebase structure, testing results, limitations, and future improvements.

This project is developed as an academic IoT prototype for:

```text
NETW1010: Internet of Things
```

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
# Complete Project Implementation Steps

This section explains the full project workflow from hardware assembly to firmware upload, backend setup, Firebase storage, dashboard testing, and final demo validation. It is placed at the beginning of the README so anyone reading the repository can understand how the project was built and how to run it end-to-end.

## Step 0 — Understand the Final System Idea

The project tracks an outdoor asset using a GPS module and two TTGO LoRa32 boards.

The final working architecture is:

```text
NEO-6M GPS
   ↓ UART
TTGO LoRa32 Sender
   ↓ LoRa radio packet
TTGO LoRa32 Receiver / Gateway
   ↓ WiFi + MQTT
MQTT Broker
   ↓ MQTT subscription
Python MQTT-to-Firebase Bridge
   ↓ HTTP request
Firebase Realtime Database
   ↓ Firebase REST reads
Dashboard V2 / Google Maps Dashboard
```

The most important design decision is that the sender and receiver do different jobs:

```text
Sender  = GPS + LoRa only
Receiver = LoRa + WiFi + MQTT gateway
```

The sender does not connect to WiFi. This keeps the moving unit simpler and more power-friendly. The receiver is the gateway that forwards data to the internet.

---

## Step 1 — Prepare the Hardware Components

The required hardware is:

| Component | Quantity | Purpose |
|---|---:|---|
| LILYGO TTGO LoRa32 board | 2 | One board is the sender, one board is the receiver/gateway |
| NEO-6M GPS module | 1 | Reads latitude, longitude, UTC time, satellites, and HDOP |
| LoRa antennas | 2 | One antenna for each TTGO LoRa32 board |
| Female-to-female jumper wires | 3 minimum | Connect GPS module to sender board |
| USB data cables | 2 | Upload firmware and power/debug boards |
| Laptop | 1 | Arduino IDE, Python backend, Firebase, dashboards |
| 3.7V LiPo battery or USB power bank | 1 | Powers sender independently during final demo |

Important hardware note:

```text
Always attach the LoRa antenna before powering the TTGO LoRa32 boards.
```

This protects the LoRa radio module and improves communication reliability.

---

## Step 2 — Assemble the Sender Hardware

The sender is the moving unit. It is placed on the asset, for example a golf car, shuttle, or moving outdoor object.

The sender contains:

```text
TTGO LoRa32 Sender + NEO-6M GPS + LoRa Antenna + Battery/Power Bank
```

### Sender Wiring

Connect the NEO-6M GPS module to the sender TTGO board as follows:

| GPS Pin | TTGO LoRa32 Sender Pin | Purpose |
|---|---|---|
| VCC | 5V | Powers the GPS module |
| GND | GND | Shared ground |
| TXD | GPIO34 | Sends GPS serial data to ESP32 |
| RXD | Not connected | Not needed because the sender only reads from GPS |

Practical wiring summary:

```text
GPS VCC  → TTGO 5V
GPS GND  → TTGO GND
GPS TXD  → TTGO GPIO34
GPS RXD  → Leave disconnected
```

Why this wiring is used:

- The GPS module sends NMEA serial sentences through its TXD pin.
- The ESP32 sender reads those GPS sentences on GPIO34.
- The GPS RXD pin is not needed because the project does not send commands back to the GPS module.
- The GPS antenna should face upward toward open sky for faster satellite lock.

### Sender Power Setup

During development, the sender can be powered through USB.

During the final demo, the sender should be powered independently using:

```text
3.7V LiPo battery
or
USB power bank
```

This proves that the sender is actually wireless and not dependent on a laptop.

### Battery Monitoring Note

The final sender firmware reads battery voltage using:

```text
GPIO35
```

Many TTGO LoRa32 boards expose battery voltage through GPIO35 using a voltage divider. If the reading is unrealistic, the exact TTGO board version may use a different battery ADC pin.

---

## Step 3 — Assemble the Receiver Hardware

The receiver is the gateway node. It does not connect to the GPS module.

The receiver hardware setup is:

```text
TTGO LoRa32 Receiver + LoRa Antenna + USB Power
```

Receiver setup steps:

1. Attach the LoRa antenna.
2. Connect the receiver TTGO board to the laptop using USB.
3. Upload the `Receiver_MQTT_v1.0` firmware.
4. Keep the receiver near the laptop or presentation area.
5. Make sure the receiver has access to WiFi after firmware upload.

The receiver listens for LoRa packets from the sender, converts them to JSON, and publishes them to MQTT over WiFi.

---

## Step 4 — Install Arduino IDE Requirements

Install the Arduino IDE, then prepare ESP32 support.

### ESP32 Board Package

In Arduino IDE:

1. Open **File → Preferences**.
2. Add the ESP32 board manager URL if not already added.
3. Open **Tools → Board → Boards Manager**.
4. Search for `esp32`.
5. Install the ESP32 board package.

Recommended board option:

```text
TTGO-LoRa32-OLED
```

Alternative board option:

```text
ESP32 Dev Module
```

### Arduino Libraries

Install these libraries from Arduino Library Manager:

```text
TinyGPSPlus
LoRa
PubSubClient
ArduinoJson
```

Library purpose:

| Library | Used By | Purpose |
|---|---|---|
| TinyGPSPlus | Sender | Parses GPS NMEA data |
| LoRa | Sender + Receiver | Sends and receives LoRa packets |
| PubSubClient | Receiver | Publishes messages to MQTT |
| ArduinoJson | Receiver | Builds MQTT JSON payload |
| WiFi.h | Receiver | ESP32 WiFi connection; included with ESP32 package |

---

## Step 5 — Upload the Final Sender Firmware

Open the final sender firmware:

```text
firmware/Sender_MultiAsset_PowerTuned_v1.0/Sender_MultiAsset_PowerTuned_v1.0.ino
```

Check the GPS pin configuration:

```cpp
#define GPS_RX_PIN 34
#define GPS_TX_PIN -1
```

Check the LoRa pin/frequency configuration:

```cpp
#define LORA_SS    18
#define LORA_RST   14
#define LORA_DIO0  26
#define LORA_BAND  868E6
```

The sender and receiver must use the same LoRa frequency:

```text
868E6
```

Select one transmission mode in the sender firmware:

```cpp
#define NORMAL_MODE
```

Available modes:

| Mode | Interval | Use Case |
|---|---:|---|
| DEMO_MODE | 3 seconds | Fast live demo |
| NORMAL_MODE | 5 seconds | Balanced operation |
| POWER_SAVING_MODE | 15 seconds | Lower transmission frequency |

Upload steps:

1. Connect the sender TTGO board to the laptop.
2. Select the correct board and COM port in Arduino IDE.
3. Upload the sender firmware.
4. Open Serial Monitor at `115200 baud`.
5. Confirm that LoRa initializes successfully.
6. Move the GPS antenna outdoors or near a window/open sky.
7. Wait for GPS characters and eventually a valid GPS fix.

Expected sender Serial Monitor output:

```text
IoT Innovators - Multi-Asset Power-Tuned Sender
Mode: No OLED / Battery Friendly Sender
Week 4 Feature: Battery Voltage Monitoring
LoRa init OK
Sender ready.
Waiting for GPS data...
LoRa Packet Sent
Battery Voltage: 3.84 V
```

After the firmware is uploaded and verified, disconnect USB and power the sender with a LiPo battery or power bank for the final demo.

---

## Step 6 — Upload the Final Receiver MQTT Firmware

Open the final receiver firmware:

```text
firmware/Receiver_MQTT_v1.0/Receiver_MQTT_v1.0.ino
```

Before uploading, update the WiFi credentials locally:

```cpp
const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
```

Check the MQTT broker settings:

```cpp
const char* MQTT_SERVER = "broker.hivemq.com";
const int MQTT_PORT = 1883;
```

Check the MQTT topics:

```text
iot-innovators/assets/all
iot-innovators/assets/<deviceID>/location
iot-innovators/gateway/status
iot-innovators/gateway/debug
```

Check the LoRa frequency:

```cpp
#define LORA_BAND 868E6
```

It must match the sender.

Upload steps:

1. Connect the receiver TTGO board to the laptop.
2. Select the correct board and COM port in Arduino IDE.
3. Upload `Receiver_MQTT_v1.0.ino`.
4. Open Serial Monitor at `115200 baud`.
5. Confirm WiFi connection.
6. Confirm MQTT connection.
7. Confirm LoRa receiver initialization.

Expected receiver Serial Monitor output:

```text
IoT Innovators LoRa MQTT Receiver
Device: receiver01
Mode: LoRa to WiFi/MQTT Gateway
WiFi connected successfully.
Connecting to MQTT broker... connected.
LoRa receiver initialized successfully.
Receiver is ready.
Waiting for LoRa packets...
```

When the sender transmits, the receiver should show:

```text
LoRa Packet Received
Payload parsed successfully.
MQTT JSON Payload:
MQTT publish successful.
```

---

## Step 7 — Create and Configure Firebase Realtime Database

Firebase is used to store the latest location and history records.

Setup steps:

1. Open Firebase Console.
2. Create a Firebase project.
3. Create a Realtime Database.
4. Copy the database URL.
5. Use that URL in the backend bridge as `FIREBASE_BASE_URL`.
6. Add simple demo database rules for testing.

Demo rules:

```json
{
  "rules": {
    "assets": {
      ".read": true,
      ".write": true
    },
    ".read": false,
    ".write": false
  }
}
```

Expected database structure:

```text
assets
 └── ASSET-03
      ├── latest
      │    ├── deviceID
      │    ├── latitude
      │    ├── longitude
      │    ├── timestamp_utc
      │    ├── battery_voltage
      │    ├── battery_status
      │    ├── rssi
      │    └── packet_count
      │
      └── history
           ├── record1
           ├── record2
           └── record3
```

For a production system, the Firebase rules should be secured using authentication or a server-side admin SDK. The open rules above are only for academic demo testing.

---

## Step 8 — Run the MQTT-to-Firebase Backend

The backend bridge subscribes to MQTT messages and uploads them to Firebase.

Open a terminal in the backend folder:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```bash
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional environment configuration:

```bash
set FIREBASE_BASE_URL=https://your-database-name.firebaseio.com
set MQTT_BROKER=broker.hivemq.com
set MQTT_PORT=1883
set MQTT_TOPIC_ALL=iot-innovators/assets/all
```

Run the backend:

```bash
python mqtt_to_firebase.py
```

Expected backend output:

```text
IoT Innovators MQTT to Firebase Bridge
Mode: MQTT Broker -> Firebase Realtime DB
Week 4: Supports optional battery_voltage field
Connected to MQTT broker.
Subscribed to topic: iot-innovators/assets/all
Waiting for MQTT messages...
```

When a packet arrives:

```text
MQTT Message Received
Normalized record:
Uploaded to Firebase successfully.
Latest path: assets/ASSET-03/latest
History path: assets/ASSET-03/history
```

The backend performs these actions:

1. Receives JSON from MQTT.
2. Validates required fields.
3. Converts numeric fields.
4. Adds dashboard-compatible aliases.
5. Calculates battery status from voltage.
6. Writes the latest data to Firebase.
7. Appends the same record to Firebase history.

---

## Step 9 — Verify the End-to-End Data Flow

At this point, all system parts should be running:

```text
Sender powered on
Receiver connected to WiFi and MQTT
Python backend running
Firebase database open
Dashboard ready
```

Check the flow in this order:

1. Sender Serial Monitor shows LoRa packets being sent.
2. Receiver Serial Monitor shows LoRa packets received.
3. Receiver Serial Monitor shows MQTT publish successful.
4. Python backend shows MQTT message received.
5. Python backend shows Firebase upload successful.
6. Firebase `assets/<deviceID>/latest` updates.
7. Firebase `assets/<deviceID>/history` grows with new records.
8. Dashboard displays the selected asset on the map.

This order is useful for debugging because it follows the exact system pipeline.

---

## Step 10 — Open Dashboard V2

Open the main final dashboard:

```text
dashboard/dashboard_v2.html
```

Use VS Code Live Server or another local web server.

Dashboard V2 should show:

- selected asset ID
- live marker
- latitude and longitude
- GPS fix status
- UTC timestamp
- satellite count
- HDOP
- RSSI
- battery voltage
- battery status
- geofence status
- history trail
- transmission health

Recommended testing steps:

1. Open Dashboard V2.
2. Select `ASSET-01`, `ASSET-02`, or `ASSET-03`.
3. Wait for Firebase data to refresh.
4. Confirm marker appears on the map.
5. Confirm battery voltage/status appears.
6. Confirm history trail appears after several records.
7. Confirm geofence status changes based on position.
8. Confirm transmission health monitor checks packet continuity.

---

## Step 11 — Open the Google Maps API Dashboard

Open:

```text
dashboard/dashboard_google_maps.html
```

This dashboard uses the same Firebase data as Dashboard V2 but displays it using the Google Maps JavaScript API.

Before testing, replace the placeholder API key locally:

```js
const GOOGLE_MAPS_API_KEY = "ENTERHERE";
```

Replace `ENTERHERE` with a real Google Maps JavaScript API key.

Important note:

```text
Do not commit a real unrestricted Google Maps API key to a public repository.
```

If the map shows a "For development purposes only" overlay, that means Google Cloud billing/prepayment is not fully active for the key. This is a Google Maps account configuration issue, not a project logic issue.

Dashboard V2 with Leaflet/OpenStreetMap remains the reliable non-billing fallback for the final live demo.

---

## Step 12 — Perform Outdoor Hardware Testing

GPS testing should be done outdoors because GPS may not get a reliable fix indoors.

Outdoor testing checklist:

1. Place the sender in an open-sky area.
2. Keep the GPS patch antenna facing upward.
3. Keep the receiver powered and connected to WiFi.
4. Make sure both LoRa antennas are attached.
5. Wait for a valid GPS fix.
6. Move the sender slowly.
7. Watch the receiver for packets.
8. Watch Firebase for latest/history updates.
9. Watch Dashboard V2 for marker movement and trail updates.

Record these observations:

- time to first GPS fix
- satellite count
- HDOP value
- RSSI value
- packet count
- missing packet count
- battery voltage
- whether the asset is inside or outside the geofence

---

## Step 13 — Validate Week 4 Features

Week 4 required polishing, testing, power behavior, and at least one additional feature.

The final system validates those requirements as follows:

| Week 4 Item | How It Was Implemented |
|---|---|
| Full-system integration | Sender → Receiver → MQTT → Python → Firebase → Dashboard |
| Firmware polish | Final sender and receiver firmware versions added |
| Backend polish | MQTT-to-Firebase bridge normalizes and stores records |
| Dashboard polish | Dashboard V2 and Google Maps dashboard show live and historical data |
| Additional feature | Transmission Health Monitor |
| Power behavior | OLED disabled, battery/power-bank sender operation, battery voltage monitoring |
| Demo readiness | Demo sequence and speaking roles documented |

### Transmission Health Monitor

The dashboard checks packet counts in Firebase history.

It displays:

```text
Latest Packet
Records Checked
Missing Packets
Transmission Status
```

During multi-asset switching, gaps can be expected because the sender rotates between asset IDs while the packet counter continues globally.

### Battery Monitoring

The sender reads battery voltage and appends it to the payload.

Battery flow:

```text
Sender battery ADC
   ↓
LoRa payload battery_voltage
   ↓
Receiver MQTT JSON
   ↓
Python backend normalization
   ↓
Firebase battery_voltage + battery_status
   ↓
Dashboard battery display
```

Battery status logic:

| Battery Voltage | Dashboard Status |
|---:|---|
| 4.00V and above | GOOD |
| 3.70V to 3.99V | NORMAL |
| 3.40V to 3.69V | LOW |
| Below 3.40V | CRITICAL |

---

## Step 14 — Run the Final Demo

Recommended final demo sequence:

1. Show the sender hardware: TTGO + GPS + antenna + battery/power bank.
2. Explain that the sender is GPS + LoRa only.
3. Show the receiver hardware connected to the laptop.
4. Explain that the receiver is LoRa + WiFi + MQTT.
5. Start the Python backend using `python mqtt_to_firebase.py`.
6. Show receiver Serial Monitor receiving LoRa packets.
7. Show MQTT publish success in the receiver Serial Monitor.
8. Show Python backend receiving MQTT data.
9. Show Firebase latest/history updating.
10. Open Dashboard V2.
11. Select the active asset.
12. Show live marker.
13. Show historical movement trail.
14. Show geofence circle and inside/outside status.
15. Show battery voltage and battery status.
16. Show transmission health monitor.
17. Mention Google Maps dashboard as the Google Maps API version.
18. Explain known limitations and future improvements.

---

## Step 15 — Common Troubleshooting

### GPS Does Not Show a Valid Fix

Possible causes:

- GPS is indoors.
- GPS antenna is not facing open sky.
- GPS TXD is not connected to GPIO34.
- GPS module does not have enough time to acquire satellites.

Fixes:

- Move outdoors.
- Face the GPS antenna upward.
- Recheck wiring.
- Wait a few minutes for first fix.
- Confirm Serial Monitor shows GPS characters being processed.

### Receiver Does Not Receive LoRa Packets

Possible causes:

- Sender and receiver use different LoRa frequencies.
- LoRa antenna is missing.
- Sender is not powered.
- Receiver firmware is not running.
- Distance or obstacles are too high.

Fixes:

- Confirm both use `868E6`.
- Attach antennas to both boards.
- Check sender Serial Monitor for "LoRa Packet Sent".
- Check receiver Serial Monitor for "Waiting for LoRa packets".
- Test at shorter distance first.

### MQTT Is Not Updating

Possible causes:

- Receiver WiFi credentials are wrong.
- MQTT broker is unreachable.
- Receiver cannot connect to WiFi.
- Public broker is temporarily unstable.

Fixes:

- Update WiFi SSID/password in receiver firmware.
- Confirm Serial Monitor says "MQTT connected".
- Use stable WiFi.
- Restart receiver and backend.

### Firebase Is Not Updating

Possible causes:

- Python backend is not running.
- Firebase URL is wrong.
- Firebase rules block writes.
- MQTT topic mismatch.

Fixes:

- Run `python mqtt_to_firebase.py`.
- Confirm backend subscribed to `iot-innovators/assets/all`.
- Confirm `FIREBASE_BASE_URL` is correct.
- Temporarily use demo Firebase rules during testing.

### Dashboard Is Empty

Possible causes:

- Firebase has no latest record.
- Wrong asset selected.
- Browser blocked local file requests.
- Dashboard Firebase URL/config does not match backend database.

Fixes:

- Use VS Code Live Server.
- Check Firebase `assets/<deviceID>/latest`.
- Select the correct asset ID.
- Confirm dashboard config points to the same Firebase database.

---

## Project Build Timeline

The project was implemented in four stages.

### Week 1 — Hardware and LoRa Foundation

Main goal:

```text
GPS → Sender → LoRa → Receiver Serial Monitor
```

Completed work:

- Connected NEO-6M GPS to TTGO sender.
- Created sender firmware v1.0.
- Created receiver firmware v1.0.
- Defined GPS/LoRa payload format.
- Tested LoRa transmission.
- Documented wiring and payload format.

### Week 2 — First End-to-End Software Flow

Main goal:

```text
Receiver Serial Output → Python Serial Bridge → Firebase → Dashboard V1
```

Completed work:

- Added `serial_to_firebase.py`.
- Created Firebase latest/history structure.
- Created Dashboard V1 using Leaflet/OpenStreetMap.
- Added basic multi-asset display.
- Tested missing GPS fix, invalid payloads, and delayed packets.

### Week 3 — MQTT, Dashboard V2, Geofence, History, Google Maps

Main goal:

```text
Receiver MQTT Gateway → MQTT Broker → Python MQTT Bridge → Firebase → Dashboard V2
```

Completed work:

- Added No-OLED sender firmware.
- Added receiver MQTT gateway firmware.
- Added `mqtt_to_firebase.py`.
- Created Dashboard V2.
- Added history trail.
- Added circular geofence.
- Added Google Maps API dashboard.
- Improved multi-asset support.

### Week 4 — Final Integration, Power Behavior, and Demo Readiness

Main goal:

```text
Final hardware + final firmware + final backend + final dashboards + final demo
```

Completed work:

- Added final multi-asset power-tuned sender.
- Added battery voltage monitoring.
- Added transmission health monitor.
- Updated backend to store battery voltage/status.
- Updated dashboards to display battery and transmission health.
- Added Week 4 documentation files.
- Added final evidence screenshots.
- Prepared final presentation and demo flow.

---


## Final System Summary

The final system includes:

- GPS-based outdoor localization using NEO-6M.
- LoRa wireless transmission from sender to receiver.
- No-OLED sender firmware to reduce unnecessary power usage.
- Multi-asset switching to demonstrate multiple tracked assets.
- Receiver MQTT gateway using WiFi.
- MQTT-to-Firebase backend bridge.
- Firebase latest and historical data storage.
- Dashboard V2 using Leaflet/OpenStreetMap.
- Google Maps JavaScript API dashboard version.
- Live marker display.
- Historical movement trail.
- Circular geofence with inside/outside warning.
- Transmission health monitor for packet gap detection.
- Battery voltage and battery status monitoring.
- Final demo setup using battery or power bank for standalone sender operation.

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
MQTT Broker
        ↓
MQTT to Firebase Bridge
        ↓
Firebase Realtime Database
        ↓
Dashboard V2 / Google Maps Dashboard
```

---

## Correct Architecture Explanation

The sender and receiver have different responsibilities.

```text
Sender = GPS + LoRa only
Receiver = LoRa + WiFi + MQTT gateway
```

The sender does **not** send data directly through WiFi. It sends GPS data through LoRa.

The receiver receives the LoRa packets and forwards them to the internet using WiFi and MQTT.

Correct explanation:

```text
The receiver receives data through LoRa and forwards it through WiFi using MQTT.
```

Incorrect explanation:

```text
LoRa sends data through WiFi.
```

---

## System Architecture

### 1. Sensing Layer

The **NEO-6M GPS module** collects outdoor location data.

It provides:

- latitude
- longitude
- UTC timestamp
- satellite count
- HDOP
- GPS fix status

The GPS module sends data to the ESP32 sender board using UART.

---

### 2. Sender Node

The sender uses a **LILYGO TTGO LoRa32** board.

The sender:

1. Reads GPS data from the NEO-6M module.
2. Checks whether the GPS fix is valid.
3. Builds a CSV payload.
4. Adds asset ID.
5. Adds battery voltage in the Week 4 firmware.
6. Sends the payload wirelessly through LoRa.

The final sender version is battery-friendly because the OLED screen is disabled.

---

### 3. LoRa Communication Layer

LoRa is used for low-power wireless communication between the moving asset and the receiver gateway.

LoRa is suitable for this project because:

- the moving asset should not require WiFi
- LoRa supports long-range communication
- LoRa is power-efficient compared to WiFi
- the sender can run independently using a battery or power bank

---

### 4. Receiver / Gateway Layer

The receiver also uses a **LILYGO TTGO LoRa32** board.

The receiver acts as a gateway:

1. Receives LoRa packets.
2. Parses the CSV payload.
3. Converts the payload into JSON.
4. Adds RSSI.
5. Adds packet count.
6. Connects to WiFi.
7. Publishes JSON messages to MQTT.

The receiver is connected to a laptop or stable power source during the demo.

---

### 5. MQTT Layer

MQTT is used between the receiver gateway and backend.

The receiver publishes asset messages to the MQTT broker.

The Python backend subscribes to the topic and uploads the received data to Firebase.

---

### 6. Backend Layer

The backend bridge is implemented in Python.

It subscribes to MQTT messages, validates them, normalizes fields, and writes data to Firebase.

The backend stores:

- latest asset location
- historical location records
- GPS fix status
- RSSI
- satellite count
- timestamp
- gateway information
- packet count
- battery voltage
- battery status
- dashboard-compatible aliases

---

### 7. Database Layer

Firebase Realtime Database stores all asset data under:

```text
assets/<deviceID>/latest
assets/<deviceID>/history
```

The latest path is used by the dashboard to show the current asset state.

The history path is used to draw the movement trail and analyze transmission health.

---

### 8. Dashboard Layer

The project includes three dashboards:

1. **Dashboard V1**  
   Week 2 basic live location dashboard.

2. **Dashboard V2**  
   Leaflet/OpenStreetMap dashboard with live marker, history trail, geofence, transmission health, and battery monitoring.

3. **Google Maps Dashboard**  
   Google Maps JavaScript API version with the same core features.

---

## Hardware Used

| Component | Purpose |
|---|---|
| NEO-6M GPS module | Collects outdoor GPS coordinates |
| LILYGO TTGO LoRa32 sender | Reads GPS and transmits LoRa packets |
| LILYGO TTGO LoRa32 receiver | Receives LoRa packets and acts as MQTT gateway |
| LoRa antennas | Improve LoRa communication |
| Female-to-female jumper wires | Connect GPS module to TTGO sender |
| USB cables | Upload firmware and power receiver |
| 3.7V 700mAh LiPo battery | Standalone sender power option |
| USB power bank | Backup standalone sender power option |
| Laptop | Programming, backend bridge, dashboards, and receiver monitoring |

---

## Final Hardware Demo Setup

### Moving Sender

The sender is placed on the moving asset, such as a golf car.

```text
TTGO Sender + NEO-6M GPS + LoRa Antenna + Battery/Power Bank
```

The sender should be independent from the laptop during the live movement demo.

The sender does not need a COM connection after the firmware is uploaded.

---

### Receiver in Presentation Hall

```text
TTGO Receiver → WiFi/MQTT → mqtt_to_firebase.py → Firebase → Dashboard
```

The receiver stays near the laptop or presentation hall.

It receives LoRa packets from the sender and forwards them to MQTT.

---

## Technologies Used

### Embedded / IoT

- ESP32
- LILYGO TTGO LoRa32
- NEO-6M GPS
- LoRa
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
- pyserial
- Firebase Realtime Database

### Frontend

- HTML
- CSS
- JavaScript
- Leaflet.js
- OpenStreetMap
- Google Maps JavaScript API

---

## Repository Structure

The repository ZIP currently contains the following confirmed structure:

```text
outdoor-asset-localization-IoT-Innovators/
│
├── README.md
├── .gitignore
│
├── firmware/
│   ├── Sender_v1.0/
│   │   └── Sender_v1.0.ino
│   ├── Sender_NoOLED_v1.0/
│   │   └── Sender_NoOLED_v1.0.ino
│   ├── Sender_MultiAsset_PowerTuned_v1.0/
│   │   └── Sender_MultiAsset_PowerTuned_v1.0.ino
│   ├── Receiver_v1.0/
│   │   └── Receiver_v1.0.ino
│   └── Receiver_MQTT_v1.0/
│       └── Receiver_MQTT_v1.0.ino
│
├── backend/
│   ├── serial_to_firebase.py
│   ├── mqtt_to_firebase.py
│   └── requirements.txt
│
├── dashboard/
│   ├── dashboard_v1.html
│   ├── dashboard_v2.html
│   └── dashboard_google_maps.html
│
├── docs/
│   ├── week_1/
│   │   ├── backend-schema.md
│   │   ├── payload-format.md
│   │   ├── week-1-test-log.md
│   │   └── wiring-reference.md
│   ├── week_2/
│   │   └── week2-test-log.md
│   ├── week_3/
│   │   ├── dashboard-v2-features.md
│   │   ├── mqtt-integration.md
│   │   └── week3-test-log.md
│   └── week_4/
│       ├── power-measurement.md
│       ├── final-integration-test-log.md
│       └── demo-speaking-roles.md
│
├── evidence/
│   ├── week_1/
│   ├── week_2/
│   ├── week_3/
│   └── week_4/
│       ├── final-dashboard-live-battery.png
│       └── gaps_detected.png
│
├── diagrams/
│   ├── Final_system_architecture.png
│   ├── week1_system-architecture.png
│   └── week3_system-architecture.png
│
├── presentation/
│   ├── IoT_Innovators_Final_Presentation.pptx
│   └── IoT_Innovators_week1_presentation.pptx
│
└── references/
    └── references.md
```

### Important Repository Audit Notes

- The final Week 4 sender folder in the uploaded ZIP is named `Sender_MultiAsset_PowerTuned_v1.0`, not `Sender_MultiAsset_PowerTuned_Battery_v1.0`.
- The final Week 4 sender still includes battery voltage monitoring; the word `Battery` simply is not part of the actual folder/file name.
- The Google Maps dashboard currently uses `ENTERHERE` as the API-key placeholder. Replace that value locally with a real Google Maps JavaScript API key when testing.
- The included Week 4 evidence files in the ZIP are `final-dashboard-live-battery.png` and `gaps_detected.png`. Additional screenshots/video can still be added if required by submission rules.

---

# Firmware Documentation

## Sender v1.0

```text
firmware/Sender_v1.0/Sender_v1.0.ino
```

This is the original sender firmware.

It reads GPS data, sends LoRa packets, and uses the onboard OLED for local display.

---

## Sender No-OLED v1.0

```text
firmware/Sender_NoOLED_v1.0/Sender_NoOLED_v1.0.ino
```

This version removes OLED usage to reduce unnecessary power consumption.

Core function:

```text
GPS → TTGO Sender → LoRa transmission
```

The sender still prints debug information through Serial Monitor when USB is connected.

---

## Sender Multi-Asset Power-Tuned Battery v1.0

```text
firmware/Sender_MultiAsset_PowerTuned_v1.0/Sender_MultiAsset_PowerTuned_v1.0.ino
```

This is the final Week 4 sender firmware.

It includes:

- No OLED operation.
- GPS reading.
- LoRa transmission.
- Multi-asset switching.
- Configurable transmission intervals.
- Battery voltage reading.
- Battery voltage added to the LoRa payload.

### Transmission Modes

| Mode | Send Interval | Purpose |
|---|---:|---|
| DEMO_MODE | 3 seconds | Fast testing/demo |
| NORMAL_MODE | 5 seconds | Balanced operation |
| POWER_SAVING_MODE | 15 seconds | Reduced transmission frequency |

### Multi-Asset Switching

The sender switches between:

```text
ASSET-01
ASSET-02
ASSET-03
```

This makes the dashboard multi-asset behavior more realistic than static simulation.

---

## Receiver v1.0

```text
firmware/Receiver_v1.0/Receiver_v1.0.ino
```

This is the Week 2 receiver firmware.

It receives LoRa packets and prints parsed output to Serial Monitor.

Receiver validation in Week 2 was completed using Serial Monitor output.

---

## Receiver MQTT v1.0

```text
firmware/Receiver_MQTT_v1.0/Receiver_MQTT_v1.0.ino
```

This is the final receiver/gateway firmware.

It performs the following:

1. Connects to WiFi.
2. Connects to MQTT broker.
3. Initializes LoRa.
4. Receives LoRa packets.
5. Parses CSV payload.
6. Supports old and new payload formats.
7. Converts payload to JSON.
8. Adds RSSI and packet count.
9. Publishes JSON to MQTT.
10. Prints debug output to Serial Monitor.

The receiver supports both:

```text
Old payload: 8 fields
New Week 4 payload: 9 fields including battery_voltage
```

---

# Payload Format

## Week 2 / Week 3 Payload

```text
deviceID,fix,latitude,longitude,timestamp_utc,satellites,hdop,uptime
```

Example:

```text
ASSET-01,1,29.992221,31.555294,2026-05-12T17:54:49Z,5,2.0,2523
```

## Week 4 Payload

```text
deviceID,fix,latitude,longitude,timestamp_utc,satellites,hdop,uptime,battery_voltage
```

Example:

```text
ASSET-03,1,29.992250,31.555190,2026-05-24T19:53:12Z,5,2.4,807,3.84
```

## Payload Fields

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
| battery_voltage | Sender battery voltage in volts |

---

# MQTT Integration

## MQTT Purpose

MQTT was added to improve the Week 2 architecture by removing the dependency on the receiver USB COM port for sending data to the backend.

In Week 2:

```text
Receiver Serial Monitor → Python Serial Bridge → Firebase
```

In the final architecture:

```text
Receiver MQTT Gateway → MQTT Broker → Python MQTT Bridge → Firebase
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

This is suitable for academic testing. A production system should use a private/authenticated MQTT broker.

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

### Gateway Debug Topic

```text
iot-innovators/gateway/debug
```

---

## MQTT JSON Payload

The receiver converts the LoRa CSV payload into JSON before publishing it to MQTT.

Example:

```json
{
  "deviceID": "ASSET-03",
  "fix": 1,
  "latitude": 29.99225,
  "longitude": 31.55519,
  "timestamp_utc": "2026-05-24T19:53:12Z",
  "satellites": 5,
  "hdop": 2.4,
  "uptime": 807,
  "battery_voltage": 3.84,
  "batteryVoltage": 3.84,
  "rssi": -30,
  "gateway": "receiver01",
  "packet_count": 807,
  "raw_payload": "ASSET-03,1,29.992250,31.555190,2026-05-24T19:53:12Z,5,2.4,807,3.84"
}
```

---

# Backend Documentation

## Serial to Firebase Bridge

```text
backend/serial_to_firebase.py
```

This was used in Week 2.

It reads receiver output from the COM port and uploads parsed location data to Firebase.

This file is kept as a legacy validation path.

---

## MQTT to Firebase Bridge

```text
backend/mqtt_to_firebase.py
```

This is the final backend bridge.

It subscribes to:

```text
iot-innovators/assets/all
```

When an MQTT message is received, it:

1. Parses the JSON payload.
2. Validates required fields.
3. Normalizes the data.
4. Adds dashboard-compatible aliases.
5. Stores battery voltage and battery status.
6. Uploads the latest asset data to Firebase.
7. Appends the record to Firebase history.

---

# Firebase Database Structure

The backend stores data under:

```text
assets/<deviceID>/latest
assets/<deviceID>/history
```

Example:

```text
assets
 └── ASSET-03
      ├── latest
      │    ├── deviceID
      │    ├── fix
      │    ├── latitude
      │    ├── longitude
      │    ├── timestamp_utc
      │    ├── satellites
      │    ├── hdop
      │    ├── uptime
      │    ├── battery_voltage
      │    ├── battery_status
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
deviceId
timestamp
timestampUTC
received_at
receivedAt
last_updated
lastUpdated
lat
lng
gps_fix
gpsFix
batteryVoltage
batteryStatus
```

---

# Dashboard Documentation

## Dashboard V1

```text
dashboard/dashboard_v1.html
```

Dashboard V1 was created during Week 2.

It displays current asset location using Firebase latest records.

---

## Dashboard V2

```text
dashboard/dashboard_v2.html
```

Dashboard V2 uses **Leaflet.js + OpenStreetMap**.

It includes:

- live marker
- history trail
- geofence circle
- inside/outside geofence warning
- multi-asset dropdown
- status panel
- automatic refresh
- Firebase latest reading
- Firebase history reading
- transmission health monitor
- battery voltage display
- battery status display

### Dashboard V2 Displayed Fields

- asset status
- device ID
- GPS fix status
- latitude
- longitude
- UTC timestamp
- satellites
- HDOP
- RSSI
- battery voltage
- battery status
- gateway
- source
- received time
- geofence status
- distance from geofence center
- history record count
- trail status
- latest packet
- records checked
- missing packets

---

## Google Maps API Dashboard

```text
dashboard/dashboard_google_maps.html
```

This file was added because Google Maps API integration is mandatory in the Week 3 plan.

It reads the same Firebase latest/history records as Dashboard V2 and implements:

- live marker using Google Maps Marker
- history trail using Google Maps Polyline
- geofence using Google Maps Circle
- inside/outside warning
- multi-asset dropdown
- automatic refresh
- Firebase latest reading
- Firebase history reading
- transmission health monitor
- battery voltage display
- battery status display

### Google Maps API Key Note

The Google Maps dashboard contains a placeholder:

```js
const GOOGLE_MAPS_API_KEY = "ENTERHERE";
```

The real API key should be pasted locally during testing.

Do not push a real unrestricted API key to a public repository.

### Google Maps Billing Note

Google Maps JavaScript API was integrated as required. During testing, the map displayed the **“For development purposes only”** overlay because Google Cloud requires active billing/prepayment to remove the development watermark.

The project keeps **Dashboard V2 using Leaflet/OpenStreetMap** as a reliable non-billing fallback for the final live demo, while the Google Maps dashboard remains included as proof of Google Maps API integration.

---

# Week 4 Additional Features

## 1. Transmission Health Monitor

The transmission health monitor was added to the dashboards.

It checks `packet_count` values stored in Firebase history.

It displays:

- latest packet count
- number of records checked
- missing packets
- transmission status

Example dashboard output:

```text
Latest Packet: 807
Records Checked: 39
Missing Packets: 281
Status: Gaps Detected
```

During multi-asset switching, gaps can be expected because the packet counter is global and shared across multiple asset IDs.

Example:

```text
Packet 800 → ASSET-01
Packet 801 → ASSET-02
Packet 802 → ASSET-03
Packet 803 → ASSET-01
```

When the dashboard filters only ASSET-03, packet numbers may appear to jump. This proves the monitor is actively checking continuity.

---

## 2. Battery Voltage Monitoring

Battery monitoring was added as part of Week 4 power behavior work.

The sender reads battery voltage and appends it to the LoRa payload.

The receiver forwards it to MQTT.

The backend stores:

```text
battery_voltage
batteryVoltage
battery_status
batteryStatus
```

The dashboards display:

```text
Battery Voltage
Battery Status
```

Observed example:

```text
Battery Voltage: 3.84 V
Battery Status: NORMAL
```

### Battery Status Logic

| Battery Voltage | Status |
|---:|---|
| 4.00V and above | GOOD |
| 3.70V to 3.99V | NORMAL |
| 3.40V to 3.69V | LOW |
| Below 3.40V | CRITICAL |

---

# Power Measurement / Power Behavior

Week 4 required power consumption measurement.

The system addresses this by:

1. Disabling OLED on the sender.
2. Supporting battery-powered sender operation.
3. Adding battery voltage monitoring.
4. Displaying battery voltage/status on the dashboard.
5. Documenting power behavior.

The sender can run using:

```text
3.7V 700mAh LiPo battery
or
USB power bank backup
```

The dashboard confirmed:

```text
Battery Voltage: 3.84 V
Battery Status: NORMAL
```

This is a power behavior indicator.

Direct current draw was not measured because a current meter or USB power meter was not available. If a current meter becomes available, power can be calculated using:

```text
Power (W) = Voltage (V) × Current (A)
```

Example:

```text
3.7V × 0.12A = 0.444W
```

---

# Installation and Setup

## 1. Arduino IDE Setup

Install the ESP32 board package in Arduino IDE.

Recommended board:

```text
TTGO-LoRa32-OLED
```

Alternative:

```text
ESP32 Dev Module
```

---

## 2. Arduino Libraries

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

## 3. Uploading the Final Sender

Open:

```text
firmware/Sender_MultiAsset_PowerTuned_v1.0/Sender_MultiAsset_PowerTuned_v1.0.ino
```

Check:

```cpp
#define GPS_RX_PIN 34
#define GPS_TX_PIN -1
#define LORA_BAND 868E6
```

Choose one transmission mode:

```cpp
#define NORMAL_MODE
```

Upload the code to the sender TTGO board.

Open Serial Monitor at:

```text
115200 baud
```

Expected output:

```text
IoT Innovators - Multi-Asset Power-Tuned Sender
Week 4 Feature: Battery Voltage Monitoring
LoRa init OK
Waiting for GPS data...
LoRa Packet Sent
Battery Voltage: 3.84 V
```

After uploading, disconnect USB and power the sender with a LiPo battery or power bank.

---

## 4. Uploading the Receiver MQTT Gateway

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
Battery Voltage: 3.84
```

---

## 5. Running the Backend

Go to the backend folder:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```bash
.\venv\Scripts\Activate.ps1
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
IoT Innovators MQTT to Firebase Bridge
Week 4: Supports optional battery_voltage field
Waiting for MQTT messages...
MQTT Message Received
Normalized record:
Uploaded to Firebase successfully.
Latest path: assets/ASSET-03/latest
History path: assets/ASSET-03/history
```

To leave the virtual environment:

```bash
deactivate
```

---

## 6. Python Requirements

The backend requirements are:

```text
pyserial
requests
paho-mqtt
```

`pyserial` is kept for the Week 2 serial bridge.  
`paho-mqtt` is used for the MQTT bridge.  
`requests` is used to upload data to Firebase.

---

## 7. Opening the Dashboards

Open dashboards using VS Code Live Server.

### Dashboard V1

```text
dashboard/dashboard_v1.html
```

### Dashboard V2

```text
dashboard/dashboard_v2.html
```

### Google Maps Dashboard

```text
dashboard/dashboard_google_maps.html
```

Full final flow:

```text
Sender_MultiAsset_PowerTuned
        ↓
LoRa
        ↓
Receiver_MQTT
        ↓
MQTT
        ↓
mqtt_to_firebase.py
        ↓
Firebase
        ↓
Dashboard V2 / Google Maps Dashboard
```

---

# Firebase Security Rules

Firebase Realtime Database should have rules that allow the academic demo to access the `assets` node while blocking unrelated paths.

Simple demo rules:

```json
{
  "rules": {
    "assets": {
      ".read": true,
      ".write": true
    },
    ".read": false,
    ".write": false
  }
}
```

These rules are acceptable for academic prototype testing but are not production-secure.

A production version should use Firebase Authentication or server-side admin credentials.

---

# Weekly Progress Summary

## Week 1 Progress

Week 1 focused on stable embedded communication.

Completed:

- Sender firmware created.
- Receiver firmware created.
- GPS module connected to sender.
- LoRa communication tested.
- Payload format documented.
- Wiring reference documented.
- Outdoor GPS-to-LoRa tests performed.
- Initial Firebase backend schema prepared.
- Evidence screenshots collected.

Evidence folder:

```text
evidence/week_1/
```

---

## Week 2 Progress

Week 2 focused on creating the first end-to-end software path.

Completed:

- Receiver output connected to Firebase using Python serial bridge.
- Firebase stores latest asset location.
- Firebase stores location history.
- Dashboard V1 created.
- Dashboard displays asset location on map.
- Dashboard supports asset selection.
- Dashboard displays coordinates and status fields.
- Edge cases handled:
  - missing GPS fix
  - delayed/stale packets
  - invalid payloads
  - multiple asset IDs

Evidence folder:

```text
evidence/week_2/
```

---

## Week 3 Progress

Week 3 improved the architecture and added the main project features beyond the basic location display.

Completed:

- Added No-OLED sender firmware.
- Added MQTT receiver/gateway firmware.
- Receiver connects to WiFi.
- Receiver publishes LoRa packets to MQTT.
- Added MQTT to Firebase bridge.
- Firebase receives data from MQTT.
- Dashboard V2 created.
- Dashboard V2 displays live marker.
- Dashboard V2 displays historical path trail.
- Dashboard V2 includes circular geofence.
- Dashboard V2 shows inside/outside geofence status.
- Dashboard V2 supports multi-asset selection.
- Dashboard V2 refreshes automatically.
- Google Maps API dashboard version added.
- Google Maps dashboard displays live marker, history trail, and geofence circle.
- Google Maps billing limitation documented.
- UTC timestamp, device ID, and received time visible.
- Week 3 documentation files created.
- Week 3 evidence screenshots collected.

Evidence folder:

```text
evidence/week_3/
```

---

## Week 4 Progress

Week 4 focused on final polishing, validation, power behavior, and demo readiness.

Completed:

- Added multi-asset switching sender behavior.
- Added power-tuned transmission modes.
- Added sender battery voltage reading.
- Updated receiver to accept battery voltage field.
- Updated backend to store battery voltage/status.
- Updated Dashboard V2 to display battery voltage/status.
- Updated Google Maps dashboard to display battery voltage/status.
- Added transmission health monitor.
- Added Firebase Week 4 test JSON.
- Added Week 4 documentation files:
  - `power-measurement.md`
  - `final-integration-test-log.md`
  - `demo-speaking-roles.md`
- Tested dashboard with live ASSET-03 data.
- Verified battery voltage appeared on dashboard.
- Verified history trail appeared on dashboard.
- Verified transmission health monitor displayed packet analysis.
- Prepared final demo plan.

Evidence folder:

```text
evidence/week_4/
```

Included Week 4 evidence files in the current ZIP:

```text
final-dashboard-live-battery.png
gaps_detected.png
```

Additional recommended evidence that can be added before final submission:

```text
final-dashboard-history-trail.png
final-firebase-latest-battery.png
final-mqtt-to-firebase-terminal.png
final-receiver-serial-monitor.png
final-sender-battery-setup.jpg
backup-demo-video-link.md
```

---

# Requirement Mapping

## Week 3 Requirement Mapping

| Week 3 Requirement | Status |
|---|---|
| Store historical coordinates | Completed |
| Show recent path trail on map | Completed in Dashboard V2 and Google Maps dashboard |
| Implement simple geofence | Completed |
| Provide warning when asset leaves zone | Completed |
| Run longer tests to check consistency | Completed / documented |
| Integrate Google Maps API into dashboard | Completed with billing limitation documented |
| Display asset location using live coordinates | Completed |
| Implement real-time updates | Completed using automatic refresh |
| Multi-asset support or simulated multi-device view | Completed |
| Stored historical data visible in database and dashboard | Completed |
| Technical documentation at least 50% complete | Completed |

---

## Week 4 Requirement Mapping

| Week 4 Requirement | Status |
|---|---|
| Full-system integration tests in realistic environment | Completed / final demo test planned |
| Fix remaining firmware/backend/dashboard bugs | Completed during Week 4 updates |
| Complete final report | Completed through README.md |
| Complete architecture visuals | Included in diagrams folder |
| Complete repository README | Completed |
| Prepare final presentation slides | Completed: `presentation/IoT_Innovators_Final_Presentation.pptx` exists in the ZIP |
| Rehearse live demo sequence | Demo roles documented |
| Record backup demo video | Not found in the uploaded ZIP; record or add a backup video link if required |
| Optional enhancements | Battery monitoring and transmission tuning added |
| Implement one additional feature | Completed: Transmission Health Monitor |
| Measure power consumption | Addressed through battery voltage monitoring and power behavior documentation |
| Final integrated system working end-to-end | Completed |
| Repository cleaned and documented | Completed in the uploaded ZIP; final commit/push still depends on repository hosting workflow |

---

# Final Demo Plan

## Demo Setup

### Sender on Golf Car

```text
TTGO Sender + GPS Module + LoRa Antenna + Battery/Power Bank
```

The sender reads GPS coordinates and transmits LoRa packets.

It does not need to stay connected to the laptop.

---

### Receiver in Presentation Hall

```text
TTGO Receiver → WiFi/MQTT → mqtt_to_firebase.py → Firebase → Dashboard
```

The receiver acts as the internet gateway.

---

## Final Demo Sequence

1. Show the sender powered independently.
2. Show the receiver connected to laptop.
3. Run `mqtt_to_firebase.py`.
4. Show receiver Serial Monitor receiving LoRa packets.
5. Show Firebase latest/history updating.
6. Open Dashboard V2.
7. Select active asset.
8. Show live marker.
9. Show history trail.
10. Show geofence circle/status.
11. Show battery voltage/status.
12. Show transmission health.
13. Explain backup Google Maps dashboard.
14. Explain limitations and future work.

---

# Design Decisions

## 1. Sender Kept as GPS + LoRa Only

The sender is attached to the moving asset, so it should remain simple and power-efficient.

Adding WiFi/MQTT to the sender would increase power usage and reduce the benefit of using LoRa.

Therefore:

```text
Sender = GPS + LoRa only
```

---

## 2. Receiver Upgraded into Gateway

The receiver is less power-sensitive and can act as the internet gateway.

Therefore:

```text
Receiver = LoRa + WiFi + MQTT
```

---

## 3. OLED Disabled in Updated Sender

The OLED display is useful for debugging but not required for final operation.

Disabling it reduces unnecessary power usage.

---

## 4. Firebase Kept as Backend

The dashboard was already working with Firebase, so the MQTT upgrade was integrated by adding an MQTT-to-Firebase bridge instead of rebuilding the dashboard from scratch.

---

## 5. Dashboard V2 Added Instead of Replacing Dashboard V1

Dashboard V1 was kept as the Week 2 version.

Dashboard V2 was added as the enhanced version with history trail, geofence, transmission health, and battery monitoring.

---

## 6. Google Maps Dashboard Added Separately

A separate Google Maps dashboard was added because the plan required Google Maps API integration.

Dashboard V2 remains the stable non-billing fallback dashboard for the final demo.

---

# Testing Results

## Successful Tests

- Sender GPS readings verified.
- LoRa packets transmitted.
- Receiver received LoRa packets.
- Receiver published MQTT messages.
- Backend received MQTT messages.
- Backend uploaded to Firebase.
- Firebase latest and history records updated.
- Dashboard displayed live marker.
- Dashboard displayed geofence circle.
- Dashboard displayed history trail.
- Dashboard displayed battery voltage/status.
- Dashboard displayed transmission health.
- Multi-asset dropdown showed multiple assets.

---

## Observed Dashboard Output

Example observed values:

```text
Device ID: ASSET-03
GPS Fix: Valid Fix
Latitude: 29.992250
Longitude: 31.555190
UTC Timestamp: 2026-05-24T19:53:12Z
Satellites: 5
HDOP: 2.4
RSSI: -30
Battery Voltage: 3.84 V
Battery Status: NORMAL
Gateway: receiver01
Source: mqtt
```

Transmission health example:

```text
Latest Packet: 807
Records Checked: 39
Missing Packets: 281
Status: Gaps Detected
```

This gap result is expected during multi-asset switching because one global packet counter is shared across multiple asset IDs.

---

# Known Limitations

- GPS fix may be slow or unavailable indoors.
- MQTT currently uses a public broker for academic testing.
- Google Maps JavaScript API requires active billing/prepayment to remove the development watermark.
- Battery voltage is a power behavior indicator, not a direct current measurement.
- Current consumption was not directly measured because no current meter was available.
- Transmission health may show expected gaps during multi-asset switching.
- The history trail may look short if the sender is stationary or if GPS points are very close together.

---

# Future Improvements

- Use a private/authenticated MQTT broker.
- Add stronger Firebase security rules using authentication.
- Host the dashboard online.
- Add a current sensor or USB power meter for direct current measurement.
- Add deeper power profiling across transmission modes.
- Add optional TTN/LoRaWAN integration if gateway access is available.
- Improve dashboard styling and add configurable geofence controls.
- Add direct MQTT WebSocket dashboard support.
- Add data export for testing and analysis.
- Add enclosure design for outdoor use.
- Add better battery estimation using percentage and discharge curves.

---

## Related Published Work

This project is related to previous IoT tracking systems that use GPS, LoRa/LoRaWAN, MQTT, and cloud databases. Johnsen et al. explored MQTT over LoRa for tracking applications. Wijayapraja et al. designed an ambulance tracking system using GPS, LoRaWAN, MQTT, Firebase, and a user-facing application. Muladi et al. developed a LoRa mesh GPS tracking system for mountain climbers, showing that LoRa can support outdoor tracking where cellular coverage is limited.
