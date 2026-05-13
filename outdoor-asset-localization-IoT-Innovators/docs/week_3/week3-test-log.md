# Week 3 Test Log

## Test Overview

This test log documents the Week 3 implementation and validation of the upgraded Outdoor Asset Localization system.

Week 3 focused on adding:

- MQTT receiver gateway
- No-OLED sender version
- Firebase history usage
- Dashboard V2
- Google Maps API dashboard
- live marker
- history trail
- geofence warning
- automatic dashboard refresh

---

## Test Information

| Field | Value |
|---|---|
| Test Date | May 12–13, 2026 |
| Project | Outdoor Asset Localization |
| Team | IoT Innovators |
| Sender Firmware | `Sender_NoOLED_v1.0.ino` |
| Receiver Firmware | `Receiver_MQTT_v1.0.ino` |
| Backend Bridge | `mqtt_to_firebase.py` |
| Main Dashboard | `dashboard_v2.html` |
| Google Maps Dashboard | `dashboard_google_maps.html` |
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
Dashboard V2 / Google Maps Dashboard
```

---

## Test 1: No-OLED Sender Firmware

### Objective

Confirm that the sender can collect GPS data and transmit LoRa packets without using the OLED display.

### Result

Passed.

---

## Test 2: MQTT Receiver Gateway

### Objective

Confirm that the receiver can receive LoRa packets and publish them to MQTT over WiFi.

### Expected Output

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

### Evidence

```text
evidence/week_3/mqtt-receiver-serial.png
```

---

## Test 3: MQTT to Firebase Bridge

### Objective

Confirm that the Python MQTT bridge receives MQTT messages and uploads them to Firebase.

### Result

Passed.

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

### Result

Passed.

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

### Result

Passed.

### Evidence

```text
evidence/week_3/firebase-history-mqtt.png
```

---

## Test 6: Dashboard V2 Live Marker

### Objective

Confirm that Dashboard V2 displays the latest asset location on the map.

### Result

Passed.

### Evidence

```text
evidence/week_3/dashboard-v2-live-marker.png
```

---

## Test 7: Dashboard V2 History Trail

### Objective

Confirm that Dashboard V2 reads historical Firebase records and draws a movement trail on the map.

### Expected Result

```text
Records Loaded: 50
Trail Status: Trail visible
```

### Result

Passed.

### Evidence

```text
evidence/week_3/dashboard-v2-history-trail.png
```

---

## Test 8: Geofence Inside Zone

### Objective

Confirm that the dashboard detects when the asset is inside the geofence.

### Expected Result

```text
Inside Zone
```

### Result

Passed.

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

### Expected Result

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

### Result

Passed.

---

## Test 11: Google Maps API Dashboard

### Objective

Confirm that a Google Maps API dashboard version was implemented.

### Dashboard File

```text
dashboard/dashboard_google_maps.html
```

### Expected Result

The dashboard should:

- load Google Maps
- read Firebase latest records
- display live asset marker
- display geofence circle
- display history trail
- show asset status panel

### Result

Passed with limitation.

The Google Maps dashboard loaded and displayed Firebase asset data, live marker, and geofence circle. However, Google Maps showed the **“For development purposes only”** overlay because Google Cloud requires billing/prepayment activation.

### Evidence

```text
evidence/week_3/dashboard-google-maps-api.png
evidence/week_3/google-maps-billing-warning.png
```

---

## Longer Transmission Test

### Objective

Run a longer test to check transmission consistency and identify data gaps.

### Suggested Duration

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
| Integrate Google Maps API | Completed with billing limitation |
| Display asset location using live coordinates | Completed |
| Implement real-time updates | Completed using automatic refresh |
| Draft documentation | Completed through Week 3 documentation files |

---

## Summary

Week 3 implementation was successfully validated.

The system now supports:

```text
Sender_NoOLED → LoRa → Receiver_MQTT → MQTT → Firebase → Dashboard V2 / Google Maps Dashboard
```

The Google Maps dashboard was added to satisfy the Google Maps API requirement, with the billing watermark limitation documented.
