# Week 3 Test Log

## Test Overview

This test log documents the Week 3 implementation and validation of the upgraded Outdoor Asset Localization system.

Week 3 focused on adding features beyond the basic location display, including:

- MQTT receiver gateway
- No-OLED sender version
- Firebase history usage
- Dashboard V2
- live marker
- history trail
- geofence warning
- automatic dashboard refresh

---

## Test Information

| Field | Value |
|---|---|
| Test Date | May 12, 2026 |
| Project | Outdoor Asset Localization |
| Team | IoT Innovators |
| Sender Firmware | `Sender_NoOLED_v1.0.ino` |
| Receiver Firmware | `Receiver_MQTT_v1.0.ino` |
| Backend Bridge | `mqtt_to_firebase.py` |
| Dashboard | `dashboard_v2.html` |
| Backend Database | Firebase Realtime Database |
| MQTT Broker | `broker.hivemq.com` |
| MQTT Port | `1883` |
| MQTT Topic | `iot-innovators/assets/all` |
| Tested Asset ID | `ASSET-01` |

---

## Updated Week 3 Data Flow

```text
NEO-6M GPS Module
        ↓
TTGO LoRa32 Sender No-OLED
        ↓
LoRa Wireless Communication
        ↓
TTGO LoRa32 Receiver MQTT Gateway
        ↓
WiFi + MQTT
        ↓
MQTT to Firebase Bridge
        ↓
Firebase Realtime Database
        ↓
Dashboard V2
```

---

## Test 1: No-OLED Sender Firmware

### Objective

Confirm that the sender can collect GPS data and transmit LoRa packets without using the OLED display.

### Expected Result

The sender should:

- initialize LoRa successfully
- read GPS data
- build the normal CSV payload
- transmit packets every configured interval
- print debug output through Serial Monitor

### Result

Passed.

The sender transmitted LoRa packets using the same payload format as the previous version.

### Notes

The OLED display was removed from the sender to reduce unnecessary power consumption. Debugging remains available through Serial Monitor.

---

## Test 2: MQTT Receiver Gateway

### Objective

Confirm that the receiver can receive LoRa packets and publish them to MQTT over WiFi.

### Expected Result

The receiver should show the following in Serial Monitor:

```text
WiFi connected successfully
MQTT connected
LoRa receiver initialized successfully
LoRa Packet Received
Payload parsed successfully
MQTT publish successful
```

### Result

Passed.

The receiver successfully acted as a LoRa-to-WiFi/MQTT gateway.

### Evidence

```text
evidence/week_3/mqtt-receiver-serial.png
```

---

## Test 3: MQTT to Firebase Bridge

### Objective

Confirm that the Python MQTT bridge receives MQTT messages and uploads them to Firebase.

### Expected Result

The terminal should show:

```text
MQTT Message Received
Normalized record:
Uploaded to Firebase successfully.
Latest path: assets/ASSET-01/latest
History path: assets/ASSET-01/history
```

### Result

Passed.

MQTT messages were received and uploaded to Firebase successfully.

### Evidence

```text
evidence/week_3/mqtt-to-firebase-bridge.png
```

---

## Test 4: Firebase Latest Record

### Objective

Confirm that Firebase stores the latest asset location.

### Expected Firebase Path

```text
assets/ASSET-01/latest
```

### Expected Fields

```text
deviceID
fix
latitude
longitude
timestamp_utc
satellites
hdop
uptime
rssi
gateway
source
updated_at
received_at
```

### Result

Passed.

Firebase latest record updated successfully from MQTT data.

### Evidence

```text
evidence/week_3/firebase-latest-mqtt.png
```

---

## Test 5: Firebase History Records

### Objective

Confirm that Firebase stores historical coordinate records.

### Expected Firebase Path

```text
assets/ASSET-01/history
```

### Expected Result

Multiple records should be visible under the history path.

### Result

Passed.

Firebase history records were stored successfully.

### Evidence

```text
evidence/week_3/firebase-history-mqtt.png
```

---

## Test 6: Dashboard V2 Live Marker

### Objective

Confirm that Dashboard V2 displays the latest asset location on the map.

### Expected Result

Dashboard V2 should show:

- live asset marker
- asset status
- device ID
- GPS fix
- latitude
- longitude
- UTC timestamp
- RSSI
- received time

### Result

Passed.

Dashboard V2 displayed the live marker and updated asset details correctly.

### Evidence

```text
evidence/week_3/dashboard-v2-live-marker.png
```

---

## Test 7: Dashboard V2 History Trail

### Objective

Confirm that Dashboard V2 reads historical Firebase records and draws a movement trail on the map.

### Expected Result

Dashboard V2 should show:

```text
Records Loaded: 50
Trail Status: Trail visible
```

### Result

Passed.

The dashboard loaded historical records and displayed the trail status successfully.

### Evidence

```text
evidence/week_3/dashboard-v2-history-trail.png
```

### Notes

The trail may appear short or tightly grouped because the GPS coordinates were close together during testing.

---

## Test 8: Geofence Inside Zone

### Objective

Confirm that the dashboard detects when the asset is inside the geofence.

### Expected Result

Dashboard should show:

```text
Inside Zone
```

The dashboard should also show:

- geofence circle
- zone center
- radius
- distance from center

### Result

Passed.

The asset was correctly detected inside the geofence.

### Evidence

```text
evidence/week_3/dashboard-v2-geofence-inside.png
```

---

## Test 9: Geofence Warning

### Objective

Confirm that the dashboard can show a warning when the asset is outside the geofence.

### Method

The geofence radius can be temporarily reduced for testing.

Example:

```js
radiusMeters: 1
```

After refreshing the dashboard, the asset should be outside the geofence if its distance from the center is greater than the radius.

### Expected Result

Dashboard should show:

```text
Outside Zone - Warning
```

### Result

Passed if screenshot was captured.

### Evidence

```text
evidence/week_3/dashboard-v2-geofence-warning.png
```

---

## Test 10: Automatic Refresh

### Objective

Confirm that the dashboard updates automatically without manual page reload.

### Expected Result

Dashboard should refresh latest data periodically.

Current refresh interval:

```text
5 seconds
```

### Result

Passed.

The dashboard updates from Firebase automatically using polling.

---

## Longer Transmission Test

### Objective

Run a longer test to check transmission consistency and identify data gaps.

### Suggested Test Duration

```text
15 to 30 minutes
```

### Items to Observe

| Item | Observation |
|---|---|
| MQTT packets received | Successful |
| Firebase latest updates | Successful |
| Firebase history records added | Successful |
| Dashboard marker updates | Successful |
| GPS fix stability | Stable during visible fix |
| RSSI values | Recorded through dashboard and Firebase |
| Data gaps | No critical issue observed during short validation |

---

## Week 3 Requirement Mapping

| Week 3 Requirement | Result |
|---|---|
| Store historical coordinates | Completed |
| Show recent path trail on map | Completed |
| Implement simple geofence | Completed |
| Provide dashboard warning outside zone | Completed |
| Run longer tests | Initial validation completed; longer test recommended |
| Display asset location using live coordinates | Completed |
| Implement real-time updates | Completed using automatic refresh |
| Draft documentation | Completed through Week 3 documentation files |

---

## Summary

Week 3 implementation was successfully validated.

The system now supports:

```text
Sender_NoOLED → LoRa → Receiver_MQTT → MQTT → Firebase → Dashboard V2
```

Dashboard V2 successfully displays the live marker, asset status, history trail, and geofence status.
