# Wiring Reference — NEO-6M GPS to TTGO LoRa32 Sender

## Hardware Used
- **GPS Module:** NEO-6M GPS
- **Sender Board:** LILYGO TTGO LoRa32
- **Receiver Board:** LILYGO TTGO LoRa32
- **Jumper Wires:** female-to-female
- **Power / Programming:** USB data cable

---

## Purpose of the Wiring
The GPS module is connected to the **sender** LoRa board using **3 jumper wires**:

- one wire for **power**
- one wire for **ground**
- one wire for **GPS serial data**

The receiver board is not connected to the GPS. It only receives LoRa packets wirelessly.

---

## GPS to Sender Connections
| GPS Pin | TTGO LoRa32 Sender Pin | Purpose |
|---|---|---|
| **VCC** | **5V** | powers the GPS module |
| **GND** | **GND** | common ground reference |
| **TXD** | **GPIO34** | sends GPS serial data to ESP32 |
| **RXD** | **Not connected** | not needed in current implementation |

---

## Practical Wiring Summary
- **GPS VCC → TTGO 5V**
- **GPS GND → TTGO GND**
- **GPS TXD → TTGO GPIO34**
- **GPS RXD → leave disconnected**

---

## Why These Connections Are Used
### 1. VCC to 5V
This wire powers the GPS module.

### 2. GND to GND
This wire provides a shared electrical ground between the GPS and the sender board.

### 3. TXD to GPIO34
This wire carries the GPS location data from the GPS module to the ESP32 on the sender board.

### 4. RXD left unconnected
The current implementation only requires one-way communication from the GPS module to the sender board, so GPS RXD is not used.

---

## GPS Data Direction
The data flow is:

**NEO-6M GPS → TTGO LoRa32 Sender → LoRa Transmission → TTGO LoRa32 Receiver**

The GPS sends NMEA serial data through **TXD**, and the sender reads it on **GPIO34**.

---

## Serial Configuration
- **GPS baud rate:** `9600`
- **Serial Monitor baud rate:** `115200`

---

## Physical Notes
- The GPS patch antenna should face **upward toward the sky** during outdoor testing.
- For fastest GPS fix, the setup should be tested outdoors in an open area.
- The sender board is powered through USB while testing.
- The receiver board is also powered through USB.
- Both the GPS module and TTGO board use **male header pins**, so **female-to-female jumper wires** are required.

---

## Receiver Node Wiring
The receiver node does **not** connect to the GPS module.

The receiver TTGO board only needs:
- USB power
- receiver firmware uploaded
- LoRa antenna attached

It listens for packets sent wirelessly by the sender node.

---

## Validation Performed
This wiring was validated through the following successful tests:

- raw GPS NMEA output detected
- valid GPS latitude/longitude fix acquired
- sender transmitted structured GPS payload over LoRa
- receiver received and parsed the same payload successfully
- RSSI values were displayed on the receiver Serial Monitor

---

## Week 1 Wiring Status
The wiring setup is complete and functional for Week 1 demonstration and testing.
