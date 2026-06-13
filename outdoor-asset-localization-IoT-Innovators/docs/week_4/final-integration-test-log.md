# Week 4 Final Integration Test Log

## Objective

The objective of this test is to validate the final outdoor asset localization system end-to-end before the final demo.

The tested workflow is:

```text
Sender GPS/LoRa → Receiver MQTT Gateway → MQTT Broker → mqtt_to_firebase.py → Firebase Realtime Database → Dashboard V2
```

## System Components Tested

| Component | Status |
|---|---|
| TTGO LoRa32 Sender | Tested |
| NEO-6M GPS Module | Tested |
| TTGO LoRa32 Receiver | Tested |
| MQTT publishing | Tested |
| MQTT-to-Firebase bridge | Tested |
| Firebase latest/history storage | Tested |
| Dashboard V2 | Tested |
| Google Maps dashboard | Tested |
| Battery monitoring | Tested |
| Transmission health monitor | Tested |
| Geofence | Tested |
| History trail | Tested |
| Multi-asset support | Tested |

## Final Test Setup

### Sender Side

```text
TTGO LoRa32 Sender
NEO-6M GPS Module
LoRa antenna
Battery or power bank
No laptop COM connection during movement
```

Sender firmware:

```text
Sender_MultiAsset_PowerTuned_Battery_v1.0
```

Main sender features:

```text
No OLED
GPS reading
LoRa transmission
Multi-asset switching
Battery voltage reporting
Power-tuned send interval
```

### Receiver Side

```text
TTGO LoRa32 Receiver
USB power from laptop
WiFi hotspot / WiFi network
MQTT publishing enabled
```

Receiver responsibilities:

```text
Receive LoRa packets
Parse CSV payload
Convert data to JSON
Add RSSI and packet_count
Publish to MQTT topic
```

### Backend Side

Backend file:

```text
backend/mqtt_to_firebase.py
```

Backend responsibilities:

```text
Subscribe to MQTT topic
Validate incoming JSON
Normalize field names
Store latest record in Firebase
Append history record in Firebase
Store battery voltage/status
```

### Dashboard Side

Dashboards tested:

```text
dashboard/dashboard_v2.html
dashboard/dashboard_google_maps.html
```

Dashboard features:

```text
Live marker
History trail
Geofence circle
Inside/outside warning
Multi-asset dropdown
Battery voltage
Battery status
Transmission health
Automatic refresh
```

## MQTT Topic

```text
iot-innovators/assets/all
```

## Firebase Structure

```text
assets/<deviceID>/latest
assets/<deviceID>/history
```

Example:

```text
assets/ASSET-03/latest
assets/ASSET-03/history
```

## Test Observations

### Dashboard V2

The dashboard successfully displayed:

```text
ASSET-03
Live status
Valid GPS fix
Latitude and longitude
UTC timestamp
Satellites
HDOP
RSSI
Battery Voltage
Battery Status
Gateway
Source
Received At
```

Observed battery example:

```text
Battery Voltage: 3.84V
Battery Status: NORMAL
```

### History Trail

Observed result:

```text
History records loaded: 39
Trail status: Trail visible
```

### Geofence

Observed result:

```text
Geofence circle visible
Asset marker inside/near the configured test zone
```

### Transmission Health

Observed result:

```text
Latest Packet: 807
Records Checked: 39
Missing Packets: 281
Status: Gaps Detected
```

This result is expected during dynamic multi-asset switching because the global packet counter is shared between multiple asset IDs. When viewing only one asset, packet_count values may appear to jump because other packets belong to other assets.

Example:

```text
Packet 800 → ASSET-01
Packet 801 → ASSET-02
Packet 802 → ASSET-03
Packet 803 → ASSET-01
```

When the dashboard filters only ASSET-03, it may detect gaps. This proves the transmission health monitor is actively checking packet continuity.

## Evidence Files to Capture

Recommended evidence screenshots/photos:

```text
evidence/week_4/final-dashboard-live-battery.png
evidence/week_4/final-dashboard-history-trail.png
evidence/week_4/final-dashboard-transmission-health.png
evidence/week_4/final-firebase-latest-battery.png
evidence/week_4/final-mqtt-to-firebase-terminal.png
evidence/week_4/final-receiver-serial-monitor.png
evidence/week_4/final-sender-battery-setup.jpg
evidence/week_4/backup-demo-video-link.md
```

## Known Limitations

1. Google Maps API may show a development watermark if billing is not fully activated.
2. Battery voltage is a power behavior indicator, not a direct current measurement.
3. Transmission gap detection may show expected gaps during multi-asset switching.
4. GPS fix quality depends on outdoor visibility and satellite reception.
5. LoRa range and RSSI depend on antenna placement, distance, and obstacles.

## Final Result

The final integrated system works end-to-end.

The system successfully demonstrates:

```text
GPS acquisition
LoRa transmission
MQTT gateway forwarding
Firebase storage
Live dashboard visualization
Historical movement trail
Geofence monitoring
Multi-asset support
Transmission health monitoring
Battery voltage monitoring
```

## Final Demo Readiness

| Requirement | Status |
|---|---|
| End-to-end system working | Completed |
| Outdoor/realistic test | Completed / To be repeated in final demo location |
| Dashboard live marker | Completed |
| History trail | Completed |
| Geofence warning | Completed |
| Multi-asset support | Completed |
| Additional feature | Completed: Transmission Health Monitor |
| Power behavior | Completed: Battery Voltage Monitoring |
| Backup video | To be recorded |
| Final slides | To be finalized |
| Final report | To be finalized |
