# Clankers Smart LoRa Signage System

## Project Description

The Clankers Smart LoRa Signage System is an IoT announcement system for
remotely updating two e-paper displays.

Users submit normal or emergency announcements through a web dashboard. The
dashboard stores the desired display states in ThingsBoard Cloud. An always-on
ESP32 gateway receives state updates from ThingsBoard over MQTT and caches
them. Each display receiver periodically wakes its LoRa radio, requests its
latest state from the gateway, updates its e-paper screen when necessary, sends
an acknowledgement, and returns the LoRa radio to sleep.

The design combines cloud-based state management with long-range, low-power
LoRa communication.

## Team

**Team name:** Clankers

**Team members:**

- Youssef Ahmed Hussein Abdelaziz
- Ahmed Hazem
- Mohamed Waleed
- Youssef El Rayes

## System Architecture

```text
User
  |
  v
Web Dashboard
  |
  | REST API over HTTPS
  v
ThingsBoard Cloud
  |  Shared attributes: desired display state
  |  Telemetry: receiver delivery status and RSSI
  |
  | MQTT over WiFi
  v
LoRa Gateway ESP32
  |
  | Addressed LoRa packets at 868 MHz
  |
  +--------------------------+
  |                          |
  v                          v
DISPLAY_1 Receiver           DISPLAY_2 Receiver
ESP32 + E-paper              ESP32 + E-paper
```

### Main Components

#### Web Dashboard

The browser interface allows users to:

- Send a normal announcement to one selected display.
- Send an emergency announcement to both displays.
- View the latest display states stored in ThingsBoard.
- Check whether the dashboard server can connect to ThingsBoard.

The dashboard backend is implemented in `web-dashboard/server.js`. It
authenticates with ThingsBoard through the REST API and reads or writes shared
attributes for `DISPLAY_1` and `DISPLAY_2`.

#### ThingsBoard Cloud

ThingsBoard acts as the persistent cloud state and communication layer.

Each display is represented by a ThingsBoard device. Its desired display state
is stored using these shared attributes:

- `tutorial`
- `course`
- `slot`
- `room`
- `message`
- `priority`
- `version`

The gateway also reports receiver acknowledgements as telemetry:

- `lastAppliedVersion`
- `lastRssi`
- `status`

#### LoRa Gateway

The gateway firmware is located at:

```text
arduino/lora_sender/lora_sender.ino
```

The gateway remains continuously powered and connected to:

- WiFi
- ThingsBoard MQTT
- LoRa receive mode

When ThingsBoard sends an attribute update, the gateway only updates its local
cache. It does not immediately transmit over LoRa. When a receiver sends a
request, the gateway responds with the cached state for that receiver.

#### Display Receivers

The receiver firmware is located at:

```text
arduino/receiver_1/receiver_1.ino
arduino/receiver_2/receiver_2.ino
```

Each receiver controls one 4.2-inch Waveshare e-paper display. Its ESP32 stays
awake, but its LoRa radio sleeps between polls.

Every 60 seconds, a receiver:

1. Wakes its LoRa radio.
2. Sends a `TYPE=REQ` packet.
3. Listens for a gateway response for up to 3 seconds.
4. Checks the received message version.
5. Refreshes the e-paper only if the version changed.
6. Sends a `TYPE=ACK` packet.
7. Puts the LoRa radio back to sleep.

Receiver 2 is offset from Receiver 1 by approximately 30 seconds to reduce
radio collisions.

## End-to-End Message Flow

### Normal Announcement

```text
1. User selects DISPLAY_1 or DISPLAY_2 and submits an announcement.
2. The dashboard server validates the announcement.
3. The server increments the selected display's version.
4. The server writes the new shared attributes to ThingsBoard.
5. ThingsBoard pushes the update to the gateway through MQTT.
6. The gateway caches the new state.
7. The selected receiver requests its state during its next poll.
8. The gateway sends the cached state over LoRa.
9. The receiver renders the state if its version changed.
10. The receiver sends an ACK.
11. The gateway publishes ACK information as ThingsBoard telemetry.
```

### Emergency Announcement

An emergency announcement is written to both ThingsBoard display devices with
the same new version and `priority` set to `EMERGENCY`.

Each receiver receives the emergency during its next scheduled poll. Emergency
messages do not bypass the polling schedule.

## Communication Protocols

### Dashboard to ThingsBoard

The Node.js server uses the ThingsBoard REST API over HTTPS to:

- Authenticate as a ThingsBoard tenant user.
- Find display devices by name.
- Read shared attributes.
- Save new shared attributes.

### ThingsBoard to Gateway

The gateway uses MQTT over WiFi.

Relevant ThingsBoard Gateway MQTT topics:

| Topic | Purpose |
| --- | --- |
| `v1/gateway/connect` | Register downstream display devices |
| `v1/gateway/attributes` | Receive shared-attribute updates |
| `v1/gateway/telemetry` | Publish receiver ACK telemetry |

### Gateway to Receivers

The gateway and receivers communicate over LoRa using text packets.

Example request:

```text
TYPE=REQ|SOURCE=DISPLAY_1|VERSION=11
```

Example data response:

```text
TYPE=DATA|TARGET=DISPLAY_1|PRIORITY=NORMAL|TUT=T01|COURSE=IoT|SLOT=10:00-11:00|ROOM=C7.201|MSG=Class starts soon.|VERSION=12
```

Example acknowledgement:

```text
TYPE=ACK|SOURCE=DISPLAY_1|VERSION=12|RSSI=-74
```

## Technologies Used

### Hardware

- Three LILYGO LoRa32 T3 V1.6.1 ESP32 boards
- Integrated LoRa radios
- Two Waveshare 4.2-inch V2 black-and-white e-paper displays
- LoRa antennas
- USB power supplies

Attach a LoRa antenna and USB power to all three LILYGO boards. The gateway
needs no external signal wiring.

Use the following wiring for both receiver e-paper displays. Set each Waveshare
4.2-inch V2 e-paper module's `BS` switch to `0`.

| E-paper pin | Female wire | Extension | Receiver LILYGO |
| --- | --- | --- | --- |
| VCC | Gray | Red | 3.3V |
| GND | Brown | Black | GND |
| DIN | Blue | Blue | IO15 |
| CLK | Yellow | Yellow | IO14 |
| CS | Orange | Orange | IO13 |
| DC | Green | Green | IO2 |
| RST | White | White | IO4 |
| BUSY | Purple | Purple | IO35 |

### Cloud and Networking

- ThingsBoard Cloud
- ThingsBoard REST API
- ThingsBoard Gateway MQTT API
- WiFi
- MQTT
- LoRa at 868 MHz

### Software

- Arduino C++
- Node.js 18 or newer
- HTML
- CSS
- Browser JavaScript

### Arduino Libraries

- `LoRa`
- `PubSubClient`
- `ArduinoJson`
- `GxEPD2`
- `Adafruit GFX Library`

## Implementation Details

### ThingsBoard State Model

ThingsBoard shared attributes are the persistent source of truth for each
display's desired state.

The gateway stores a temporary in-memory copy using a `DisplayState` structure.
If the gateway restarts, the dashboard server periodically republishes the
ThingsBoard states so the gateway can rebuild its cache.

### Version-Based Rendering

Every announcement has an increasing numeric `version`.

Receivers remember the last version they applied and only refresh the e-paper
when a different version arrives. This avoids unnecessary e-paper refreshes and
reduces power usage.

### Pull-Based LoRa Delivery

The gateway does not push every ThingsBoard update immediately. Receivers pull
their latest state according to their own schedules.

This allows the receiver LoRa radios to remain asleep most of the time.

### Stable Poll Scheduling

Polling is scheduled using fixed 60-second intervals. Processing time does not
reset the schedule after every poll, which prevents the polling times from
slowly drifting.

### Input Validation

The dashboard server:

- Requires every announcement field.
- Removes characters that conflict with the LoRa packet format.
- Limits individual field lengths.
- Rejects announcements that would exceed the LoRa packet-size limit.

### Credential Protection

Real credentials are stored only in ignored local files:

```text
web-dashboard/.env
arduino/lora_sender/secrets.h
```

Safe placeholder templates are provided:

```text
web-dashboard/.env.example
arduino/lora_sender/secrets.example.h
```

API keys, access tokens, and other real credentials must never be committed.

## Project Structure

```text
.
|-- arduino/
|   |-- lora_sender/
|   |   |-- lora_sender.ino
|   |   `-- secrets.example.h
|   |-- receiver_1/
|   |   `-- receiver_1.ino
|   `-- receiver_2/
|       `-- receiver_2.ino
|-- web-dashboard/
|   |-- .env.example
|   |-- index.html
|   |-- script.js
|   |-- server.js
|   `-- styles.css
`-- README.md
```

## Setup Summary

### ThingsBoard

1. Create a ThingsBoard gateway device and enable **Is gateway**.
2. Create normal devices named exactly `DISPLAY_1` and `DISPLAY_2`.
3. Copy the gateway device access token into a local `secrets.h`.
4. Configure the dashboard's local `.env` with ThingsBoard credentials.

### Gateway Firmware

Create `arduino/lora_sender/secrets.h` based on `secrets.example.h`:

```cpp
#pragma once

const char* kWifiSsid = "your-wifi-name";
const char* kWifiPassword = "your-wifi-password";
const char* kThingsBoardHost = "mqtt.eu.thingsboard.cloud";
const char* kGatewayAccessToken = "your-thingsboard-gateway-access-token";
```

Upload `arduino/lora_sender/lora_sender.ino` to the gateway ESP32.

### Receiver Firmware

Upload:

- `arduino/receiver_1/receiver_1.ino` to Receiver 1.
- `arduino/receiver_2/receiver_2.ino` to Receiver 2.

Use **ESP32 Dev Module** as the board configuration.

### Dashboard

```bash
cd web-dashboard
cp .env.example .env
```

Edit the newly created `web-dashboard/.env` file:

```dotenv
PORT=8080
THINGSBOARD_URL=https://eu.thingsboard.cloud
THINGSBOARD_USERNAME=your-thingsboard-email
THINGSBOARD_PASSWORD=your-thingsboard-password
THINGSBOARD_JWT=
DISPLAY_1_NAME=DISPLAY_1
DISPLAY_2_NAME=DISPLAY_2
```

| Variable | Purpose |
| --- | --- |
| `PORT` | Local port used by the dashboard server |
| `THINGSBOARD_URL` | ThingsBoard Cloud REST API base URL |
| `THINGSBOARD_USERNAME` | ThingsBoard tenant account email |
| `THINGSBOARD_PASSWORD` | ThingsBoard tenant account password |
| `THINGSBOARD_JWT` | Optional existing JWT, used instead of username/password |
| `DISPLAY_1_NAME` | Name of the first ThingsBoard display device |
| `DISPLAY_2_NAME` | Name of the second ThingsBoard display device |

The dashboard server loads this file at startup. It uses either
`THINGSBOARD_JWT` or the username/password pair to authenticate with the
ThingsBoard REST API.

The real `.env` file must remain local because it can contain account
credentials. Only `.env.example`, which contains placeholders, should be
committed.

Start the dashboard:

```bash
npm start
```

Open:

```text
http://localhost:8080
```

## Progress Achieved

The following functionality has been implemented:

- Web dashboard for normal and emergency announcements
- ThingsBoard REST authentication
- Reading and writing display shared attributes
- Version generation for display updates
- Periodic state republishing for gateway recovery
- ThingsBoard Gateway MQTT connection
- MQTT shared-attribute subscription
- Gateway-side state caching
- Addressed LoRa request and response packets
- Two standalone receiver firmware sketches
- 60-second low-power receiver polling
- 30-second receiver polling offset
- Three-second receiver response timeout
- Version-based e-paper rendering
- Receiver ACK packets
- ACK telemetry publishing to ThingsBoard
- WiFi and MQTT reconnection handling
- Local credential files excluded from Git
- Successful compilation of the gateway and both receiver sketches

## Assumptions and Design Decisions

- The system contains exactly two display receivers: `DISPLAY_1` and
  `DISPLAY_2`.
- The gateway remains continuously powered.
- The gateway remains connected to WiFi, MQTT, and LoRa receive mode.
- Only the receiver LoRa radios sleep; the receiver ESP32 processors remain
  awake.
- "Once every minute" means every 60 seconds from receiver startup, not aligned
  to real-world clock minute boundaries.
- Receiver polls are staggered by approximately 30 seconds to reduce
  collisions.
- Messages, including emergencies, remain cached until each receiver's next
  poll.
- Only the latest desired state for each display is required.
- ThingsBoard shared attributes are the persistent desired state.
- ThingsBoard telemetry represents receiver delivery confirmation.
- E-paper refreshes should be minimized because they are slow and consume
  additional energy.
- LoRa payloads use a simple pipe-separated text format for readability and
  debugging.

## Current Limitations

- Receiver ESP32 processors do not enter deep sleep.
- Message delivery can take up to one polling interval.
- Emergency messages are delivered at the next poll rather than immediately.
- The gateway cache is stored only in RAM.
- LoRa packets are not encrypted at the application layer.
- The implementation currently targets two fixed display IDs.

## How to Run the Project

### 1. Prepare ThingsBoard Cloud

Sign in to `https://eu.thingsboard.cloud` and create:

1. A device named `LoRa Signage Gateway`.
2. Enable **Is gateway** for that device.
3. Two normal devices named exactly `DISPLAY_1` and `DISPLAY_2`.

Copy the access token of `LoRa Signage Gateway`. This token is used only by the
gateway ESP32 for MQTT communication. It cannot be used by the web dashboard
for ThingsBoard REST requests.

### 2. Configure and Upload the Gateway

Create the ignored local secrets file from its safe template:

```bash
cp arduino/lora_sender/secrets.example.h arduino/lora_sender/secrets.h
```

Edit `arduino/lora_sender/secrets.h`:

```cpp
#pragma once

const char* kWifiSsid = "your-wifi-name";
const char* kWifiPassword = "your-wifi-password";
const char* kThingsBoardHost = "mqtt.eu.thingsboard.cloud";
const char* kGatewayAccessToken = "your-gateway-device-access-token";
```

Using the Arduino IDE:

1. Install `LoRa`, `PubSubClient`, and `ArduinoJson`.
2. Select **ESP32 Dev Module**.
3. Open `arduino/lora_sender/lora_sender.ino`.
4. Connect the gateway LILYGO board and upload the sketch.
5. Open Serial Monitor at `115200` baud and confirm that WiFi, ThingsBoard
   MQTT, and LoRa initialize successfully.

### 3. Configure and Upload the Receivers

Install `GxEPD2` and `Adafruit GFX Library` in addition to the `LoRa` library.
Wire both e-paper displays using the table in the Hardware section above.

Using **ESP32 Dev Module**:

1. Upload `arduino/receiver_1/receiver_1.ino` to the `DISPLAY_1` receiver.
2. Upload `arduino/receiver_2/receiver_2.ino` to the `DISPLAY_2` receiver.
3. Open Serial Monitor at `115200` baud to verify radio wake, request,
   response, ACK, and radio sleep messages.

Receiver 1 starts polling after approximately 3 seconds. Receiver 2 starts
approximately 30 seconds later. Both then poll every 60 seconds.

### 4. Configure the Web Dashboard

Node.js 18 or newer is required.

Create the ignored dashboard environment file:

```bash
cd web-dashboard
cp .env.example .env
```

Configure `web-dashboard/.env` using one of the following authentication
methods.

For a normal ThingsBoard email/password account:

```dotenv
PORT=8080
THINGSBOARD_URL=https://eu.thingsboard.cloud
THINGSBOARD_USERNAME=your-thingsboard-email
THINGSBOARD_PASSWORD=your-thingsboard-password
THINGSBOARD_JWT=
DISPLAY_1_NAME=DISPLAY_1
DISPLAY_2_NAME=DISPLAY_2
```

For an account that uses GitHub or another external login provider, place a
current ThingsBoard **user JWT** in `THINGSBOARD_JWT` and leave the password
empty: (it is different from device JWT, keep in mind use the eu based thingsboard not the global one) (this is the way i did it jwt + username)

```dotenv
PORT=8080
THINGSBOARD_URL=https://eu.thingsboard.cloud
THINGSBOARD_USERNAME=
THINGSBOARD_PASSWORD=
THINGSBOARD_JWT=your-current-thingsboard-user-jwt
DISPLAY_1_NAME=DISPLAY_1
DISPLAY_2_NAME=DISPLAY_2
```

The dashboard user JWT is different from the gateway device access token. User
JWTs can expire or be revoked, so replace the JWT if ThingsBoard returns a
`401 Invalid username or password` response.

Never commit `web-dashboard/.env` or
`arduino/lora_sender/secrets.h`; both can contain real credentials.

### 5. Start and Use the Dashboard

From `web-dashboard/`, run:

```bash
npm start
```

The project has no external npm dependencies, so `npm install` is not required.

Open:

```text
http://localhost:8080
```

To access the dashboard from another device on the same WiFi network, use the
computer's local IP address:

```text
http://<computer-local-ip>:8080
```

Send a normal announcement to one display or send an emergency announcement to
both displays. ThingsBoard updates the gateway cache immediately, but each
receiver displays the message only at its next scheduled poll.

### 6. Verify the Complete Flow

Confirm the following:

1. The dashboard starts without a ThingsBoard authentication error.
2. Sending a message creates a new shared-attribute version in ThingsBoard.
3. The gateway Serial Monitor reports that it cached the updated display state.
4. The target receiver wakes at its next poll and receives the new version.
5. The e-paper refreshes only when the received version changed.
6. The receiver sends an ACK.
7. ThingsBoard telemetry shows `lastAppliedVersion`, `lastRssi`, and `status`.

Expected gateway Serial output:

```text
ThingsBoard MQTT connected.
Cached ThingsBoard state for DISPLAY_1, version=1
LoRa received: TYPE=REQ|SOURCE=DISPLAY_1|VERSION=0
LoRa sent: TYPE=DATA|TARGET=DISPLAY_1|...
ACK from DISPLAY_1, version=1
```

Expected receiver Serial output:

```text
Low-power LoRa receiver: DISPLAY_1
LoRa radio wake.
LoRa sent: TYPE=REQ|SOURCE=DISPLAY_1|VERSION=0
LoRa received: TYPE=DATA|TARGET=DISPLAY_1|...
Applied version 1
LoRa sent: TYPE=ACK|SOURCE=DISPLAY_1|VERSION=1|RSSI=-...
LoRa radio sleep.
```
note : device 1 wakes up at 3 seconds and then every 60 seconds , device 2 wakes up at 33 seconds and then every 60 seconds  , Emergency sends to both , and deciding device Type in dashboard decides which device to communicate to if you are sneding normally
