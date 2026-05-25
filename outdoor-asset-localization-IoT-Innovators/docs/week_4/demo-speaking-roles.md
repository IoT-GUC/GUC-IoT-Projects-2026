# Week 4 Demo Speaking Roles

## Objective

This document defines the final demo speaking roles so the team can present the project clearly and avoid overlap.

## Suggested Presentation Flow

```text
1. Project overview
2. System architecture
3. Hardware setup
4. Sender firmware
5. Receiver MQTT gateway
6. Backend and Firebase
7. Dashboard features
8. Week 4 features
9. Live demo
10. Limitations and future work
```

## Team Members

Update the names below if needed.

| Team Member | Suggested Role |
|---|---|
| Adam Amr Mongy | Project overview, architecture, final demo flow |
| Farah Khaled | Sender hardware, GPS module, battery setup |
| Kareem Emad Gad | Receiver MQTT gateway and MQTT broker flow |
| Rahma Mohamed | Dashboard V2, geofence, history trail, battery display |
| George Ehab | Testing, transmission health, power behavior, limitations |

## Detailed Speaking Notes

### 1. Project Overview — Adam

Main points:

```text
Our project is an outdoor asset localization system.
The asset carries a GPS-enabled LoRa sender.
The receiver acts as a gateway and forwards data to the cloud.
The dashboard visualizes the asset location in real time.
```

Suggested script:

```text
Our system tracks outdoor assets using GPS and LoRa. The sender reads GPS coordinates and transmits them wirelessly. The receiver receives LoRa packets and forwards them through MQTT. A Python bridge stores the data in Firebase, and the dashboard displays the live location, movement history, geofence status, transmission health, and battery information.
```

### 2. Hardware and Sender — Farah

Main points:

```text
TTGO LoRa32 sender
NEO-6M GPS module
LoRa antenna
Battery or power bank
No OLED to reduce power usage
```

Suggested script:

```text
The sender consists of a TTGO LoRa32 board connected to a NEO-6M GPS module. The OLED is disabled to reduce unnecessary power usage. The sender can run from a 3.7V LiPo battery or a power bank, so it does not need to stay connected to the laptop during movement.
```

### 3. Receiver MQTT Gateway — Kareem

Main points:

```text
Receiver listens for LoRa packets
Parses CSV payload
Publishes JSON to MQTT
Adds RSSI and packet_count
Supports battery_voltage field
```

Suggested script:

```text
The receiver receives LoRa packets from the sender and converts the CSV payload into JSON. It then publishes the message to the MQTT broker. The receiver also adds signal strength using RSSI and a packet counter, which helps us evaluate transmission reliability.
```

### 4. Backend and Firebase — Kareem / Adam

Main points:

```text
mqtt_to_firebase.py subscribes to MQTT
Validates messages
Normalizes field names
Stores latest and history
```

Firebase paths:

```text
assets/<deviceID>/latest
assets/<deviceID>/history
```

Suggested script:

```text
The Python backend subscribes to the MQTT topic and receives the JSON messages. It validates the data, normalizes field names, and stores the latest record and historical records in Firebase. The latest path is used for the live marker, while the history path is used for the trail.
```

### 5. Dashboard Features — Rahma

Main points:

```text
Live marker
History trail
Geofence circle
Multi-asset dropdown
Firebase live updates
```

Suggested script:

```text
Dashboard V2 reads from Firebase and shows the selected asset on the map. It supports multiple assets through the dropdown. It also draws a history trail from stored coordinates and shows a geofence circle with an inside/outside warning.
```

### 6. Week 4 Features — George / Rahma

Main points:

```text
Transmission Health Monitor
Battery Voltage Monitoring
Battery Status
```

Suggested script:

```text
For Week 4, we added two important validation features. First, the transmission health monitor checks packet counts from Firebase history to detect possible data gaps. Second, the sender now reports battery voltage, and the dashboard displays battery voltage and battery status. This helps us observe power behavior during outdoor testing.
```

### 7. Live Demo Flow — Adam

Live demo checklist:

```text
1. Show sender powered by battery or power bank.
2. Show receiver connected to laptop.
3. Run mqtt_to_firebase.py.
4. Show Firebase latest/history updating.
5. Open Dashboard V2.
6. Select current asset.
7. Show live marker.
8. Show history trail.
9. Show geofence status.
10. Show battery voltage/status.
11. Show transmission health.
```

Suggested script:

```text
Now we will run the final workflow. The sender is operating independently and sending GPS data through LoRa. The receiver receives the packet and publishes it to MQTT. The backend uploads it to Firebase, and the dashboard updates automatically.
```

### 8. Limitations and Future Work — George

Main points:

```text
GPS accuracy depends on outdoor signal quality.
Google Maps API may require billing activation.
Transmission gaps may appear during multi-asset switching.
Battery voltage is not direct current measurement.
Future work can include TTN integration and improved power profiling.
```

Suggested script:

```text
Some limitations remain. GPS accuracy depends on satellite visibility, and Google Maps API requires billing activation for full clean rendering. Transmission health may detect expected gaps during multi-asset switching because packet counts are shared across asset IDs. For future work, we can integrate TTN and use a current sensor or USB power meter for more accurate power consumption measurement.
```

## Backup Demo Video

If live conditions are unstable, use the backup video.

The video should show:

```text
Sender powered independently
Receiver receiving LoRa packets
MQTT-to-Firebase bridge running
Firebase latest/history updating
Dashboard V2 showing live marker, trail, geofence, battery, and transmission health
```

Recommended file:

```text
evidence/week_4/backup-demo-video-link.md
```

## Final Reminder

Each speaker should keep their section short and focused.

Recommended total demo time:

```text
7 to 10 minutes
```

The most important message:

```text
The final system works end-to-end from GPS sender to dashboard, with Week 4 validation features for transmission health and battery monitoring.
```
