# Payload Format — Week 1

## Overview
The sender node transmits GPS data over LoRa using a **comma-separated text payload**. This payload is designed to be:
- easy to read in Serial Monitor
- easy to parse on the receiver side
- suitable for later backend/database storage
- extendable for dashboard and multi-asset support

## Implemented Payload Structure
`deviceID,fix,latitude,longitude,timestamp_utc,satellites,hdop,uptime`

## Example Payload
`ASSET-01,1,29.992180,31.555286,2026-04-28T19:11:13Z,5,1.7,4338`

## Field Description
| Field | Meaning |
|---|---|
| **deviceID** | identifier of the tracked asset/device |
| **fix** | GPS fix status (`1` = valid GPS fix, `0` = no valid fix) |
| **latitude** | GPS latitude in decimal format |
| **longitude** | GPS longitude in decimal format |
| **timestamp_utc** | UTC timestamp of the GPS reading |
| **satellites** | number of satellites currently used/visible |
| **hdop** | horizontal dilution of precision, indicating GPS accuracy quality |
| **uptime** | sender uptime in seconds since boot |

## Purpose of Each Field
### deviceID
Used to identify the asset being tracked. This supports future multi-asset tracking and dashboard filtering.

### fix
Shows whether the GPS currently has a valid location lock:
- `1` = valid fix
- `0` = invalid / no fix

### latitude / longitude
The main location values transmitted by the sender.

### timestamp_utc
Records the time of the GPS reading in UTC format. This will help later for:
- database storage
- timeline view
- historical movement trail

### satellites
Shows how many satellites are currently being used/seen by the GPS.

### hdop
Helps indicate the quality of the GPS reading. Lower HDOP generally means better accuracy.

### uptime
Shows how long the sender has been running since boot. Useful for debugging and system monitoring.

## Receiver Parsing
The receiver node parses the payload in this same order:

`deviceID,fix,latitude,longitude,timestamp_utc,satellites,hdop,uptime`

This allows the receiver to display:
- the raw packet
- the parsed values
- RSSI of the received transmission

## Example Interpretation
Payload:
`ASSET-01,1,29.992205,31.555269,2026-04-28T19:12:48Z,5,1.7,4433`

Interpretation:
- **deviceID** = `ASSET-01`
- **fix** = `1` → valid GPS fix
- **latitude** = `29.992205`
- **longitude** = `31.555269`
- **timestamp_utc** = `2026-04-28T19:12:48Z`
- **satellites** = `5`
- **hdop** = `1.7`
- **uptime** = `4433 s`

## Behavior When GPS Fix Is Not Available
If the GPS fix is not available:
- the `fix` field becomes `0`
- coordinates may remain invalid or fallback to placeholder values
- timestamp may be reported as `NA`

Example invalid-fix payload:
`ASSET-01,0,NA,NA,NA,0,99.9,120`

## Why a Text-Based Payload Was Used
A text-based payload was selected in Week 1 because it is:
- easy to debug in Serial Monitor
- easy to document
- simple to parse on the receiver
- suitable for rapid prototyping

In later stages, the payload could be optimized or encoded more compactly if needed.

## Week 1 Status
The current Week 1 implementation already supports this payload structure in the sender firmware and successfully parses it in the receiver firmware.

This confirms:
- payload generation works
- LoRa transmission works
- receiver-side parsing works

## Notes for Future Extensions
This payload format can later support:
- storage in a backend/database
- dashboard map updates
- historical movement trail
- geofence logic
- multi-asset tracking

No structural changes are required for these future extensions beyond backend integration.