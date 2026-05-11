# Backend Schema — Week 1

## Overview
For Week 1, the backend is not yet fully implemented, but the data structure is already defined so that received LoRa packets can later be stored in a consistent way.

The backend will store location records received from the sender node after they are parsed by the receiver or the ingestion path.

A simple structure is preferred for the early phase of the project so that it is easy to:
- save location data
- query the latest position
- support historical movement trail
- support future dashboard and geofence features

---

## Recommended Backend Option
**Preferred option:** Firebase Realtime Database

### Why this option was selected
Firebase Realtime Database is suitable because it:
- is easy to set up quickly
- works well for prototype-level IoT projects
- supports structured JSON-like data
- is easy to integrate with a web dashboard
- allows simple retrieval of latest and historical records

If needed later, this can be replaced with:
- a lightweight backend API + database
- another cloud database solution

---

## Core Data Model
Each received packet should be stored as a location record containing:
- device ID
- GPS fix status
- latitude
- longitude
- UTC timestamp
- satellites
- HDOP
- uptime
- optional RSSI
- optional server-side receive time

---

## Suggested Record Structure
```json
{
  "deviceId": "ASSET-01",
  "fix": 1,
  "latitude": 29.992205,
  "longitude": 31.555269,
  "timestampUtc": "2026-04-28T19:12:48Z",
  "satellites": 5,
  "hdop": 1.7,
  "uptime": 4433,
  "rssi": -24,
  "receivedAt": "2026-04-28T19:12:50Z"
}

## Week 1 Completion Status

Backend choice has been finalized as **Firebase Realtime Database**.

A Realtime Database instance was created and the initial schema was initialized successfully under the `assets` node, including:
- `latest`
- `history`

This completes the Week 1 requirement of finalizing the backend choice and initializing the initial backend schema.