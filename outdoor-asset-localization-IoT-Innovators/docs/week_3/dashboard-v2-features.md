# Dashboard V2 and Google Maps Features

## Overview

Dashboard V2 was created as part of the Week 3 project requirements. It extends the Week 2 dashboard by adding a live marker, historical movement trail, and geofence warning.

A separate Google Maps API dashboard was also added because the Week 3 plan requires Google Maps API integration.

Both dashboards read data from Firebase Realtime Database. The data is updated through the MQTT pipeline:

```text
Sender_NoOLED → LoRa → Receiver_MQTT → MQTT Broker → mqtt_to_firebase.py → Firebase → Dashboard
```

---

## Dashboard Files

### Dashboard V2

```text
dashboard/dashboard_v2.html
```

This is the main Week 3 dashboard using Leaflet.js and OpenStreetMap.

### Google Maps Dashboard

```text
dashboard/dashboard_google_maps.html
```

This is the Google Maps API version created to satisfy the mandatory Google Maps integration requirement.

---

## Dashboard V2 Features

Dashboard V2 implements:

- live asset marker
- history trail
- geofence circle
- inside/outside geofence warning
- multi-asset dropdown
- Firebase latest data reading
- Firebase history data reading
- automatic refresh every 5 seconds

---

## Google Maps API Dashboard

The Google Maps API version reads the same Firebase data as Dashboard V2.

It implements:

- live marker using Google Maps Marker
- history trail using Google Maps Polyline
- geofence using Google Maps Circle
- inside/outside warning
- multi-asset selection
- automatic refresh
- Firebase latest/history reading

---

## Google Maps API Billing Note

Google Maps JavaScript API was integrated as required. During testing, the map displayed the **“For development purposes only”** overlay because Google Cloud requires active billing/prepayment to remove the development watermark.

The implementation is correct from the code side, and the dashboard successfully displays:

- Firebase live asset data
- map marker
- geofence circle
- status panel

The Leaflet/OpenStreetMap Dashboard V2 remains available as a reliable non-billing fallback for the final live demo.

---

## Main Features Implemented

### 1. Live Asset Marker

The dashboards display the latest asset location on the map using the most recent coordinates stored in Firebase.

The latest location is read from:

```text
assets/<deviceID>/latest
```

Example:

```text
assets/ASSET-01/latest
```

---

### 2. History Trail

The dashboards read historical coordinates from Firebase and draw a movement trail on the map.

The history records are read from:

```text
assets/<deviceID>/history
```

---

### 3. Geofence Circle

A simple circular geofence was added.

Example configuration:

```js
const GEOFENCE = {
  name: "Test Zone",
  centerLat: 29.99222,
  centerLng: 31.55529,
  radiusMeters: 200
};
```

---

### 4. Inside / Outside Geofence Warning

If the asset is inside the selected radius, the dashboard shows:

```text
Inside Zone
```

If the asset moves outside the radius, the dashboard shows:

```text
Outside Zone - Warning
```

---

### 5. Multi-Asset Dropdown

The dashboards include an asset selection dropdown and load available assets from:

```text
assets/
```

Current tested asset:

```text
ASSET-01
```

---

## Week 3 Requirement Mapping

| Week 3 Requirement | Dashboard Status |
|---|---|
| Display asset location on map using live coordinates | Completed |
| Implement real-time updates | Completed using automatic refresh |
| Store historical coordinates | Completed in Firebase history |
| Show recent path trail on map | Completed |
| Implement simple geofence | Completed |
| Provide warning when asset leaves zone | Completed |
| Multi-asset support | Completed using asset dropdown |
| Stored historical data visible on dashboard | Completed |
| Integrate Google Maps API | Completed with billing limitation noted |

---

## Evidence

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
dashboard-google-maps-api.png
google-maps-billing-warning.png
```

---

## Notes

The asset stayed close to the same location during testing, so the history trail may appear short or tightly grouped on the map. This is expected because the GPS coordinates are close together.
