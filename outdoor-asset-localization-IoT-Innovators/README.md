# Outdoor Asset Localization

## Project Overview
This project implements an IoT-based outdoor asset localization system using a **NEO-6M GPS module** and **two LILYGO TTGO LoRa32 boards**. The goal is to track the location of an outdoor asset by acquiring live GPS coordinates on a sender node, transmitting them wirelessly over **LoRa**, and receiving/parsing them on a receiver node.

The project is designed as a low-cost prototype for academic demonstration and later extension into a dashboard-based monitoring system with history trail and geofence support.

---

## System Flow
**NEO-6M GPS Module → TTGO LoRa32 Sender → LoRa Wireless Link → TTGO LoRa32 Receiver → Backend / Dashboard (next phase)**

---

## Hardware Used
- **1 × NEO-6M GPS module**
- **2 × LILYGO TTGO LoRa32 boards**
  - one board as **sender**
  - one board as **receiver**
- **Female-to-female jumper wires**
- **USB data cables**
- Laptop for programming, testing, and Serial Monitor output

---

## Current Week 1 Status
## Week 1 Deliverables Covered
This repository currently supports the following Week 1 deliverables:

- stable firmware for both sender and receiver
- documented wiring reference
- documented payload format
- verified GPS-to-LoRa transmission
- screenshots and test logs showing successful operation
- backend choice finalized as Firebase Realtime Database
- initial backend schema created and initialized

This confirms successful **end-to-end GPS-to-LoRa communication**.

---

## Firmware Files
### Sender
`firmware/Sender_v1.0/Sender_v1.0.ino`

### Receiver
`firmware/Receiver_v1.0/Receiver_v1.0.ino`


---

## Sender Function
The sender node:
- reads live GPS data from the NEO-6M module
- checks whether a valid GPS fix exists
- extracts coordinates and status values
- builds a structured LoRa payload
- transmits the payload periodically over LoRa

The sender payload includes:
- device ID
- GPS fix status
- latitude
- longitude
- UTC timestamp
- satellite count
- HDOP
- uptime

---

## Receiver Function
The receiver node:
- listens for LoRa packets
- reads incoming payloads
- parses each field
- prints the received data on the Serial Monitor
- displays RSSI for link quality monitoring

---

## Wiring Reference
### GPS to Sender LoRa Board
| GPS Pin | TTGO LoRa32 Sender Pin | Purpose |
|---|---|---|
| **VCC** | **5V** | powers the GPS module |
| **GND** | **GND** | common ground reference |
| **TXD** | **GPIO34** | sends GPS serial data to ESP32 |
| **RXD** | **Not connected** | not needed in current implementation |

### Wiring Notes
- The GPS module sends serial data through **TXD**
- The ESP32 listens on **GPIO34**
- GPS **RXD** is not required because communication is one-way from GPS to sender
- The GPS patch antenna should face upward toward the sky during testing
- Both TTGO boards are powered through USB

---

## Payload Format
### Current Implemented Payload Structure
```text
deviceID,fix,latitude,longitude,timestamp_utc,satellites,hdop,uptime