# Indoor Asset Localization Using LoRa

**Team:** Sandy George, Marina Medhat, Youssef Khalil, Rubina Sameh
**Planning Period:** April 23, 2026 – May 20, 2026

---

## Project Overview

In many buildings, assets such as lab devices, tools, and office equipment are frequently moved, misplaced, or left in the wrong area, wasting time and interrupting work. This project implements an indoor asset tracking prototype using LoRa wireless communication to detect an asset and estimate its approximate location inside a building.

The prototype uses **two LoRa modules**:
- One ESP32-LoRa module acting as a **transmitter tag** attached to a test asset
- One ESP32-LoRa module acting as a **fixed receiver and gateway**

Based on the Received Signal Strength Indicator (RSSI) of incoming packets, the backend classifies the asset into one of four proximity zones and displays its estimated location on a live dashboard.

---

## System Architecture

| Component | Role in Prototype | Scalable Extension |
|-----------|------------------|--------------------|
| LoRa Transmitter Tag | Attached to one test asset; sends periodic beacon packets containing asset ID, packet counter, and battery voltage | Additional tags can be attached to more assets |
| ESP32 + LoRa Receiver/Gateway | Fixed at one indoor location; receives packets, measures RSSI/SNR, forwards data to backend over Wi-Fi | More receiver nodes installed in different rooms enable true zone triangulation |
| Wi-Fi / Network | Carries readings from ESP32 gateway to backend via HTTP POST | Same link supports multiple gateways |
| FastAPI Backend + SQLite | Stores asset ID, RSSI, SNR, battery, timestamp, and estimated zone; runs zone classification logic; exposes REST API | Can support multiple assets, multi-node fusion, alerts, and history analytics |
| React Dashboard | Displays estimated zone on a floor map, live RSSI bar, history chart, stats, and adjustable thresholds | Can show multiple assets, room maps, search, and alert rules |

**Data flow:**
1. Transmitter sends `ASSET_ID|PKT:N|BAT:V` every 3 seconds
2. Receiver captures packet, reads RSSI and SNR
3. Receiver forwards reading to backend via HTTP POST
4. Backend stores reading and estimates coarse zone from RSSI thresholds
5. Dashboard polls backend every 3 seconds and updates floor map, status, and charts

---

## Hardware

### LoRa RF Parameters (must match on both boards)

| Parameter | Value |
|-----------|-------|
| Frequency | 868 MHz (Europe/Egypt ISM band) |
| Sync Word | 0xA5 (private network — rejects foreign LoRa packets) |
| Spreading Factor | SF7 |
| Signal Bandwidth | 125 kHz |
| Coding Rate | 4/5 |
| TX Power | 14 dBm |

### ESP32 Pin Mapping (TTGO / Heltec ESP32 LoRa v2)

| Signal | GPIO |
|--------|------|
| SCK | 5 |
| MISO | 19 |
| MOSI | 27 |
| LoRa CS | 18 |
| LoRa RST | 23 |
| LoRa IRQ | 26 |
| Battery ADC | 35 (1/2 voltage divider) |

The receiver also drives a 128×64 SSD1306 OLED display over I2C (address 0x3C) showing asset ID, RSSI, SNR, zone, and timestamp in real time.

---

## How to Run

### 1. Backend

```bash
cd Just-Do-IoT
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at: `http://localhost:8000/docs`

### 2. Firmware

Open `Project/Project_Sender/Project_Sender.ino` and `Project/Project_Receiver/Project_Receiver.ino` in the Arduino IDE.

In `Project_Receiver.ino`, update:
```cpp
const char* WIFI_SSID     = "your_network_name";
const char* WIFI_PASSWORD = "your_password";
const char* BACKEND_URL   = "http://YOUR_PC_LOCAL_IP:8000/telemetry";
```

Flash each sketch to its respective ESP32 board.

### 3. Dashboard

```bash
cd localization-dashboard
npm install
npm start
```

Dashboard opens at `http://localhost:3000`.

---

## API Reference

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/telemetry` | Receive a reading from the ESP32 receiver |
| GET | `/overview` | Latest reading + status for every asset |
| GET | `/assets` | List all known asset IDs |
| GET | `/assets/{id}/latest` | Latest reading for one asset |
| GET | `/assets/{id}/history?limit=40` | Recent N readings for one asset |
| GET | `/stats` | Per-asset summary (total packets, avg/best/worst RSSI, avg SNR, avg battery) |
| GET | `/thresholds` | Current RSSI zone thresholds |
| PUT | `/thresholds` | Update zone thresholds at runtime |
| DELETE | `/assets/{id}` | Clear all readings for an asset |
| GET | `/health` | Health check + total reading count |

---

## RSSI Zone Thresholds

| Zone | RSSI Range | Meaning |
|------|-----------|---------|
| Same Room | ≥ −60 dBm | Asset is in the same room as the receiver |
| Nearby Room | ≥ −80 dBm | Asset is one room away |
| Same Floor | ≥ −100 dBm | Asset is on the same floor but further away |
| Out of Range | < −100 dBm | Asset is not detectable |

Thresholds are calibrated experimentally and can be adjusted live via the dashboard "Thresholds" button or `PUT /thresholds` without restarting anything.

---

## Asset Status Logic

| Status | Condition |
|--------|-----------|
| Active | Last packet received less than 15 seconds ago |
| Idle | Last packet received 15–60 seconds ago |
| Out of Range | Last packet received more than 60 seconds ago |

---

## Week-by-Week Progress

### Week 1 — Hardware Bring-up (Apr 23–29)
- Assigned hardware roles: one board as transmitter tag, one as fixed receiver/gateway
- Defined packet format: `ASSET_ID|PKT:N|BAT:V`
- Programmed transmitter to send periodic beacons every 3 seconds
- Programmed receiver to capture packets and log asset ID, RSSI, and SNR to serial
- Configured LoRa RF parameters (SF7, BW125, CR4/5, 14 dBm, SyncWord 0xA5) identically on both boards
- Initialized FastAPI backend project and SQLite schema

### Week 2 — Wi-Fi Forwarding and Calibration (Apr 30–May 6)
- Connected receiver to Wi-Fi; implemented HTTP POST to backend on each received packet
- Created database schema storing asset ID, RSSI, SNR, battery, zone, timestamp, and received_at
- Verified end-to-end data pipeline: transmitter → receiver → backend → database
- Collected RSSI samples at multiple distances and defined zone thresholds (−60 / −80 / −100 dBm)
- Built React dashboard with live asset overview, status pills, RSSI bars, and multi-asset support

### Week 3 — Zone Logic and Dashboard Integration (May 7–13)
- Implemented server-side zone classification using calibrated thresholds
- Added asset status logic (Active / Idle / Out of Range) based on time since last packet
- Built SVG floor map on the dashboard highlighting the active zone with animated glow
- Added RSSI history chart with zone reference lines
- Added recent readings table, per-asset stats panel, and live threshold editor
- Verified end-to-end system: transmitter → receiver → backend → dashboard with 3-second auto-refresh

### Week 4 — Testing, Tuning, and Finalization (May 14–20)
- Ran repeated experiments at selected indoor positions and recorded zone prediction accuracy
- Tuned RSSI thresholds using the live `PUT /thresholds` endpoint to improve consistency
- Measured practical system indicators: packet reception rate, update delay (~3 s), zone-estimation consistency
- Measured sender power consumption: idle draw between transmissions and peak draw during TX burst
- Documented prototype limitations and future scaling path
- Packaged firmware, backend, and dashboard for submission

---

## Additional Feature — Live Threshold Tuning

The backend exposes a `PUT /thresholds` endpoint that lets the team adjust zone boundaries at runtime without restarting the backend or reflashing firmware. The dashboard surfaces this as a "Thresholds" panel in the header, allowing all three zone cutoffs to be edited and saved with one click. This was especially useful during Week 4 calibration experiments where thresholds needed to be refined repeatedly based on observed RSSI values in the test environment.

---

## Known Limitations

- **Single receiver — no triangulation.** With only one fixed receiver node, the system can only estimate a coarse zone based on signal strength, not a precise (x, y) coordinate. True triangulation requires at least three receivers.
- **RSSI is environment-dependent.** Walls, furniture, and people between the tag and receiver cause signal variations that shift readings between zones. Thresholds calibrated in one room may not transfer to another.
- **Single asset tag.** Only one physical transmitter is available, so multi-asset tracking is demonstrated with one real device.
- **No sleep mode on sender.** The transmitter sends continuously every 3 seconds with no power saving, which drains the battery faster than a production design would.

---

## Future Work

- Add more ESP32-LoRa receiver nodes at fixed positions throughout the building to enable weighted RSSI triangulation
- Attach additional transmitter tags to more assets for true multi-asset tracking
- Implement deep-sleep on the sender between transmissions to extend battery life
- Add server-side alerting when an asset leaves an expected zone or goes out of range
- Replace coarse zone estimation with a fingerprinting or Kalman-filter approach for finer location accuracy
- Store calibration profiles per environment so thresholds can be loaded/switched quickly

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Firmware | Arduino (C++) — LoRa, WiFi, HTTPClient, Adafruit SSD1306 |
| Backend | Python 3, FastAPI, SQLite, Uvicorn |
| Dashboard | React, Recharts |
| Communication | LoRa 868 MHz (RF), HTTP/JSON (Wi-Fi) |
| Database | SQLite (`assets.db`) |
