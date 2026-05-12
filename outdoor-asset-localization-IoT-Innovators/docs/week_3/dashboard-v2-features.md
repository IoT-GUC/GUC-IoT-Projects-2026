# Dashboard V2 Features

## Overview

Dashboard V2 was created as part of the Week 3 project requirements. It extends the Week 2 dashboard by adding a live marker, historical movement trail, and geofence warning.

The dashboard reads data from Firebase Realtime Database. The data is updated through the new MQTT pipeline:

```text
Sender_NoOLED → LoRa → Receiver_MQTT → MQTT Broker → mqtt_to_firebase.py → Firebase → Dashboard V2
```

---

## Dashboard File

```text
dashboard/dashboard_v2.html
```

---

## Main Features Implemented

### 1. Live Asset Marker

Dashboard V2 displays the latest asset location on the map using the most recent coordinates stored in Firebase.

The latest location is read from:

```text
assets/<deviceID>/latest
```

Example:

```text
assets/ASSET-01/latest
```

The marker updates automatically when new data reaches Firebase.

---

### 2. History Trail

Dashboard V2 reads historical coordinates from Firebase and draws a movement trail on the map.

The history records are read from:

```text
assets/<deviceID>/history
```

The dashboard uses recent valid latitude and longitude records to draw a path line on the map.

This helps show the previous movement of the asset instead of only showing the latest position.

---

### 3. Geofence Circle

A simple circular geofence was added to the dashboard.

The geofence has:

- center latitude
- center longitude
- radius in meters

The current geofence configuration is located inside the JavaScript section of `dashboard_v2.html`.

Example:

```js
const GEOFENCE = {
  name: "Test Zone",
  centerLat: 29.99222,
  centerLng: 31.55529,
  radiusMeters: 200
};
```

The circular zone is shown visually on the map.

---

### 4. Inside / Outside Geofence Warning

The dashboard calculates the distance between the latest asset location and the geofence center.

If the asset is inside the selected radius, the dashboard shows:

```text
Inside Zone
```

If the asset moves outside the radius, the dashboard shows:

```text
Outside Zone - Warning
```

This satisfies the Week 3 requirement for a simple geofence warning.

---

### 5. Multi-Asset Dropdown

Dashboard V2 includes an asset selection dropdown.

The dashboard loads available assets from:

```text
assets/
```

This allows the user to select which asset to view.

Current tested asset:

```text
ASSET-01
```

This supports multi-asset tracking and also allows simulated multi-device support if more asset IDs are added to Firebase.

---

### 6. Firebase Latest Data Reading

The dashboard reads the latest asset information from Firebase and displays it in the status panel.

Displayed fields include:

- Device ID
- GPS fix status
- Latitude
- Longitude
- UTC timestamp
- Satellites
- HDOP
- RSSI
- Gateway
- Source
- Received At

---

### 7. Firebase History Data Reading

Dashboard V2 reads historical location records from Firebase.

This allows the dashboard to display:

- number of records loaded
- history trail status
- recent path trail on the map

The dashboard currently uses the most recent valid history records to keep the map readable.

---

### 8. Automatic Refresh

Dashboard V2 refreshes automatically.

Current refresh interval:

```text
Every 5 seconds
```

This allows the map marker, status panel, history trail, and geofence result to update without manually reloading the page.

---

## Map Library

Dashboard V2 uses:

```text
Leaflet.js + OpenStreetMap
```

This was used instead of Google Maps API to avoid API key and billing requirements while still providing:

- live map visualization
- asset marker
- history trail
- geofence circle
- inside/outside warning

This is suitable for the current academic prototype.

---

## Dashboard V2 Evidence

Recommended screenshots are stored under:

```text
evidence/week_3/
```

Suggested files:

```text
dashboard-v2-live-marker.png
dashboard-v2-geofence-inside.png
dashboard-v2-geofence-warning.png
dashboard-v2-history-trail.png
dashboard-v2-status-panel.png
```

---

## Week 3 Requirement Mapping

| Week 3 Requirement | Dashboard V2 Status |
|---|---|
| Display asset location on map using live coordinates | Completed |
| Implement real-time updates | Completed using automatic refresh |
| Store historical coordinates | Completed in Firebase history |
| Show recent path trail on map | Completed |
| Implement simple geofence | Completed |
| Provide warning when asset leaves zone | Completed |
| Multi-asset support or simulated multi-device view | Completed using asset dropdown |
| Stored historical data visible on dashboard | Completed |

---

## Notes

The asset stayed close to the same location during testing, so the history trail may appear short or tightly grouped on the map. This is expected because the GPS coordinates are close together. Moving the sender over a longer distance will make the trail more visible.
