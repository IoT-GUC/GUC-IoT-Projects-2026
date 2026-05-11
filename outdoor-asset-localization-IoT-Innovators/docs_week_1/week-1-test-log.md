# Week 1 Test Log

## Overview
This document summarizes the main Week 1 hardware and communication tests completed for the **Outdoor Asset Localization** project.

The purpose of these tests was to verify that:
- the GPS module can acquire valid live coordinates
- the sender node can build and transmit a structured LoRa payload
- the receiver node can receive and parse the transmitted packet successfully
- the system is stable enough to move into backend and dashboard integration in the next phase

## Test Setup

### Hardware Used
- **1 × NEO-6M GPS module**
- **1 × LILYGO TTGO LoRa32 sender**
- **1 × LILYGO TTGO LoRa32 receiver**
- **Female-to-female jumper wires**
- **USB data cables**
- Laptop for Arduino IDE and Serial Monitor

### Wiring Used
- **GPS VCC → TTGO 5V**
- **GPS GND → TTGO GND**
- **GPS TXD → TTGO GPIO34**
- **GPS RXD → Not connected**

### Serial Settings
- **GPS baud rate:** `9600`
- **Serial Monitor baud rate:** `115200`

### LoRa Link
- Sender transmits over **868 MHz**
- Receiver listens and parses the payload through LoRa

## Test 1 — GPS Raw Data Check

### Objective
Confirm that the GPS module is powered correctly and sending raw NMEA data.

### Result
**Successful**

### Evidence
Raw GPS output appeared in Serial Monitor with NMEA sentences such as:
- `$GPGGA`
- `$GPRMC`
- `$GPGSV`

### Observation
The GPS initially produced data with no valid fix, then later acquired a valid fix outdoors under open sky.

## Test 2 — GPS Valid Fix Acquisition

### Objective
Confirm that the GPS module can obtain a valid position fix and produce real latitude and longitude values.

### Result
**Successful**

### Example Output
`Latitude: 29.992158`  
`Longitude: 31.555333`  
`Satellites: 4`

### Observation
- GPS fix required outdoor placement
- patch antenna needed to face upward
- valid coordinates and satellite count were confirmed

## Test 3 — Sender Payload Transmission

### Objective
Confirm that the sender node reads live GPS data and transmits a structured LoRa payload.

### Result
**Successful**

### Example Sender Output
`Sent: ASSET-01,1,29.992200,31.555292,2026-04-28T18:54:48Z,5,1.7,3353`  
`Current fix: 29.992200, 31.555292`

### Additional Sender Status Example
`Sentences with fix: 6150`  
`Failed checksum: 0`  
`Location valid: YES`  
`Satellites: 5`  
`HDOP: 1.69`  
`Date valid: YES`  
`Time valid: YES`

### Observation
The sender successfully:
- read live GPS data
- built the structured payload
- transmitted the payload periodically over LoRa

## Test 4 — Receiver Packet Reception and Parsing

### Objective
Confirm that the receiver node receives the LoRa packet and parses all payload fields correctly.

### Result
**Successful**

### Example Receiver Output
`----- PACKET -----`  
`Raw: ASSET-01,1,29.992204,31.555288,2026-04-28T19:09:48Z,5,1.7,4253`  
`RSSI: -25`  
`Parsed: YES`  
`ID: ASSET-01`  
`Fix: 1`  
`Lat: 29.992204`  
`Lng: 31.555288`  
`UTC: 2026-04-28T19:09:48Z`  
`Sats: 5`  
`HDOP: 1.7`  
`Uptime: 4253`  
`------------------`

### Observation
The receiver successfully:
- received the LoRa packet
- read RSSI
- parsed all payload fields correctly

## Issue Encountered During Testing

### Receiver OLED Initialization Problem
The receiver initially failed when OLED initialization was enabled.

### Symptom
The board printed OLED initialization debug lines and then reset with a watchdog error.

### Resolution
The OLED was temporarily disabled in the receiver code to allow stable LoRa reception and packet parsing through the Serial Monitor.

### Outcome
After removing OLED initialization from the receiver path, the receiver worked correctly and received packets successfully.

## Summary of Week 1 Results
Week 1 testing confirms that the core hardware communication chain is working successfully:

**NEO-6M GPS → TTGO Sender → LoRa Transmission → TTGO Receiver**

### Confirmed Achievements
- raw GPS data received
- valid GPS fix acquired
- sender built and transmitted structured payloads
- receiver received and parsed payloads
- RSSI values recorded
- screenshots/logs collected as evidence

## Week 1 Conclusion
The Week 1 prototype successfully demonstrates:
- real GPS data acquisition
- reliable LoRa transmission
- receiver-side packet parsing
- readiness for the next phase of backend and dashboard integration

The system is now stable enough to proceed to:
- backend selection and storage setup
- dashboard implementation
- historical movement trail
- geofence feature development