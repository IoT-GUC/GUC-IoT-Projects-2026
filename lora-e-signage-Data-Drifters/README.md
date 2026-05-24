# LoRa-Based E-Signage for University Campus

**NETW1010 — Team: Data Drifters**

Amgad Tahoun · Nopheir George · Ahmed Salama · Hazem Elnoamy · Abdullah Khaled

---

## Overview

University campuses struggle to keep students and staff informed in real time. Printed signs go out of date quickly, and updating them manually wastes time and resources. **LoRa E-Signage** solves this by deploying wireless display nodes across campus that can be updated instantly from a web dashboard or mobile app — with no cables, no complex infrastructure, and no manual effort.

An administrator types a message on the dashboard, clicks **Send**, and it appears on every e-ink display board on campus within seconds. All traffic over the air is AES-128 encrypted, so only authorised boards can read the packets.

---

## System Architecture

```
┌─────────────────┐     MQTT/WebSocket      ┌──────────────────┐
│  Web Dashboard  │ ──────────────────────► │                  │
│  (Browser)      │                         │   HiveMQ Cloud   │
├─────────────────┤                         │   MQTT Broker    │
│  Mobile App     │ ──────────────────────► │                  │
│  (iOS/Android)  │                         └────────┬─────────┘
└─────────────────┘                                  │ MQTT TCP
                                                     ▼
                                          ┌──────────────────────┐
                                          │  Board 1 – Gateway   │
                                          │  LilyGO LoRa32       │
                                          │  WiFi + OLED status  │
                                          │  AES-128 encrypt     │
                                          └──────────┬───────────┘
                                                     │ LoRa 868 MHz
                                                     │ (encrypted, 3× burst)
                                                     ▼
                                          ┌──────────────────────┐
                                          │  Board 2 – Display   │
                                          │  LilyGO LoRa32       │
                                          │  Deep sleep 30 s     │
                                          │  AES-128 decrypt     │
                                          └──────────┬───────────┘
                                                     │ SPI
                                                     ▼
                                          ┌──────────────────────┐
                                          │  Waveshare 4.2"      │
                                          │  E-Ink Display       │
                                          │  400 × 300 px        │
                                          └──────────────────────┘
```

**Communication flow:** Dashboard / Mobile App → HiveMQ MQTT Broker → Board 1 (WiFi) → LoRa 868 MHz → Board 2 → E-Ink Display

---

## Hardware

| Component | Details |
|---|---|
| 2× LilyGO LoRa32 V1.6.1 | ESP32-PICO-D4, 240 MHz, WiFi + BT, built-in LoRa SX1276 |
| Waveshare 4.2" e-Paper V2 | 400 × 300 px, Rev 2.2, 4-wire SPI (BS pin = 0) |
| LoRa antennas | 868 MHz, one per board |

---

## Features

### Core

- **End-to-end encrypted LoRa** — AES-128-CBC with PKCS#7 padding. Packets are Base64-encoded for ASCII transport. Foreign boards without the shared key are silently rejected via padding validation.
- **Burst transmission** — Board 1 sends every message 3× with 300 ms gaps, ensuring Board 2's listen window reliably catches at least one copy.
- **Power-saving sleep cycle** — Board 2 wakes every 30 seconds, listens for a full 30-second window, then returns to deep sleep (~10 µA). The e-ink display holds its image with zero power while the board sleeps.
- **Catch-up re-broadcast** — Board 1 re-transmits the last encrypted message every 28 seconds so a waking Board 2 always receives the latest announcement, even if it was asleep when the message was first sent.
- **Burst deduplication** — Board 2 tracks the last rendered message per wake cycle; burst duplicates are detected and skipped so the display refreshes exactly once per unique message.
- **WiFi fallback** — if Board 1 cannot connect to WiFi within 30 seconds, it enters fallback mode and broadcasts a default message over LoRa every 5 seconds.
- **MQTT retained messages** — the last published message is stored on the broker so new subscribers always receive current content immediately on connect.

### Display Layout

The e-ink screen is divided into three zones:

```
┌─────────────────────────────────────────────────────────┐  ← top border
│ CAMPUS ANNOUNCEMENT                        ┌──────────┐ │
│                                            │   GUC    │ │  ← header
│                                            │  UPDATE  │ │
├─────────────────────────────────────────────────────────┤  ← divider
│                                                         │
│  Message text rendered here with word-wrap              │  ← body
│  and consistent 28 px line height                       │
│                                                         │
├─────────────────────────────────────────────────────────┤  ← footer rule
│ RSSI: -67 dBm                                       #5  │  ← footer
└─────────────────────────────────────────────────────────┘
```

**Emergency mode** — prefix any message with `EMERGENCY:` (e.g. `EMERGENCY:Fire drill at 14:00`). The header changes to `! EMERGENCY ALERT !`, the GUC badge fills solid black with `! ALERT !`, and the message renders in bold.

### Web Dashboard

A single-page browser interface that connects to HiveMQ over MQTT WebSocket. Features:

- Live message counter (total sent, alerts sent, nodes online)
- Normal / Emergency priority toggle with colour-coded UI
- 220-character limit with live count
- Sent message history with timestamps
- Real-time e-ink preview tab — renders exactly what the physical display will show, updating as you type

### Mobile App

A lightweight mobile application for Android that gives administrators the ability to send announcements from a phone without needing access to the web dashboard.

**What it does:**

- Connects to the HiveMQ broker on launch
- Provides a text field for composing announcements
- Toggle between Normal and Emergency priority
- One-tap Send publishes to `guc/datasignage/display`
- Connection status indicator (connected / disconnected / sending)
- In-memory history of recently sent messages

**MQTT topic:** `guc/datasignage/display`  
**Emergency prefix:** `EMERGENCY:<message text>`

---

## Software Stack

| Layer | Technology |
|---|---|
| Board firmware | Arduino IDE, C++ |
| LoRa radio | LoRa by Sandeep Mistry |
| E-ink driver | GxEPD2 by Jean-Marc Zingg |
| OLED driver | Adafruit SSD1306 + GFX |
| Encryption | AESLib by idolpx (AES-128-CBC) |
| MQTT client (Board 1) | PubSubClient |
| MQTT broker | HiveMQ public cloud (broker.hivemq.com) |
| Web dashboard | HTML / CSS / JavaScript (MQTT.js over WebSocket) |
| Mobile app | Flutter / React Native (MQTT client library) |

---

## Repository Structure

```
/
├── board1_sender_encrypted.ino       # Gateway node firmware (Board 1)
├── board2_receiver_encrypted_sleep.ino  # Display node firmware (Board 2)
├── dashboard/
│   └── index.html                    # Web admin dashboard
├── mobile_app/                       # Mobile application source
└── README.md
```

---

## Setup & Flashing

### 1. Install Arduino Libraries

Open Arduino IDE → **Tools → Manage Libraries** and install:

| Library | Author |
|---|---|
| LoRa | Sandeep Mistry |
| GxEPD2 | Jean-Marc Zingg |
| Adafruit SSD1306 | Adafruit |
| Adafruit GFX | Adafruit |
| PubSubClient | Nick O'Leary |
| AESLib | idolpx |

### 2. Board Settings

**Tools → Board → ESP32 Arduino → ESP32 Dev Module**

| Setting | Value |
|---|---|
| Upload Speed | 115200 |
| CPU Frequency | 240 MHz |
| Flash Size | 4MB |
| Partition Scheme | Default 4MB with spiffs |

> **macOS tip:** if the upload fails with `StopIteration` at 921600 baud, set Upload Speed to **115200** under Tools. The CP2102 USB chip on the LilyGO is unstable at maximum baud on macOS.

### 3. Change the Shared Key

Before deploying, update `kAesKey` and `kAesIv` in **both** firmware files to your own private values. They must be byte-for-byte identical on both boards.

```cpp
// In both .ino files — change these 32 bytes before flashing
static const uint8_t kAesKey[16] = { 0x??, ... };
static       uint8_t kAesIv[16]  = { 0x??, ... };
```

### 4. Flash Board 1 (Gateway)

1. Open `board1_sender_encrypted.ino`
2. Update `ssid` and `password` to your WiFi network
3. Select the correct port under **Tools → Port**
4. Click Upload (hold BOOT button when `Connecting...` appears if needed)

### 5. Wire and Flash Board 2 (Display)

Wire the e-ink display (BS switch = 0 for 4-line SPI):

| E-Paper wire | LilyGO pin |
|---|---|
| VCC (gray) | 3.3V |
| GND (brown) | GND |
| DIN (blue) | IO15 |
| CLK (yellow) | IO14 |
| CS (orange) | IO13 |
| DC (green) | IO2 |
| RST (white) | IO4 |
| BUSY (purple) | not connected |

Then flash `board2_receiver_encrypted_sleep.ino` the same way as Board 1.

### 6. Open the Web Dashboard

Open `dashboard/index.html` in any browser. It connects to HiveMQ over WebSocket automatically. Type a message and click **Broadcast**.

---

## MQTT Reference

| Parameter | Value |
|---|---|
| Broker | `broker.hivemq.com` |
| TCP port | `1883` |
| WebSocket port | `8884` (TLS) |
| Topic | `guc/datasignage/display` |
| Auth | none (public broker) |
| Normal message | any plain text string |
| Emergency message | `EMERGENCY:<text>` |

---

## Verifying Encryption

Open Serial Monitor at 115200 baud on Board 1. When a message is published you will see:

```
MQTT received: Library closed today
Sending (encrypted, 3x burst):
R2l3Q7hXmP1zQa9B...==
```

On Board 2's Serial Monitor:

```
Packet [RSSI -67 dBm] raw: R2l3Q7hXmP1zQa9B...==
Decrypted: Library closed today
```

To confirm rejection of foreign packets, temporarily change one byte of `kAesKey` on Board 2 only. Board 2 will print `PKCS#7 mismatch — ignoring packet` and the display will not update. Restore the key after testing.

---


## Team

| Name | ID |
|---|---|
| Amgad Tahoun | 55-0419 |
| Nopheir George | 55-4846 |
| Ahmed Salama | 55-11762 |
| Hazem Elnoamy | 55-7506 |
| Abdullah Khaled | 55-5418 |

**Course:** NETW1010 — German University in Cairo
