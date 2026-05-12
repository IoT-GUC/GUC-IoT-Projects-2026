# Week 3 MQTT Integration

## Objective

The goal of this update is to improve the Week 2 communication architecture by removing the dependency on the USB COM port for forwarding receiver data to the backend.

In Week 2, the receiver printed LoRa packets to the Serial Monitor, and a Python script read the receiver output through the laptop COM port. This worked successfully for validation, but it depended on a laptop being physically connected to the receiver.

In Week 3, the receiver is upgraded into a WiFi/MQTT gateway. The TTGO LoRa32 receiver now receives LoRa packets, parses them, connects to WiFi, and publishes the parsed location data to an MQTT broker.

---

## Previous Week 2 Flow

```text
GPS Module
   ↓
TTGO LoRa32 Sender
   ↓ LoRa
TTGO LoRa32 Receiver
   ↓ USB COM Port
Python Serial Bridge
   ↓
Firebase Realtime Database
   ↓
Dashboard

A No-OLED sender firmware version was added to reduce unnecessary power consumption. The OLED display was removed because the sender only needs to collect GPS data and transmit it through LoRa. Debugging is still available through the Serial Monitor during testing.