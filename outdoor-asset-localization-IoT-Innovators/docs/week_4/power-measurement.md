# Week 4 Power Measurement / Power Behavior

## Objective

The objective of this document is to record the sender power setup and power behavior observations for the final outdoor asset localization demo.

Week 4 requires power consumption measurement. In this project, we added a practical power behavior feature by monitoring and forwarding the sender battery voltage through the full system pipeline.

## Power Setup

The moving sender unit is powered independently from the laptop.

Final sender setup:

```text
TTGO LoRa32 Sender
NEO-6M GPS Module
LoRa Antenna
3.7V 700mAh LiPo Battery or USB Power Bank Backup
```

The receiver remains connected to the laptop in the presentation hall.

Receiver setup:

```text
TTGO LoRa32 Receiver
USB power from laptop
WiFi/MQTT connection
Serial Monitor for validation
```

## Battery Used

```text
Battery type: 1-cell LiPo battery
Nominal voltage: 3.7V
Capacity: 700mAh
Connection: TTGO onboard 2-pin battery socket
```

A USB power bank can also be used as a stable backup power source if the LiPo battery is unstable during the final demo.

## Week 4 Battery Monitoring Feature

The sender firmware was updated to read battery voltage and append it to the LoRa payload.

Old payload format:

```text
deviceID,fix,latitude,longitude,timestamp_utc,satellites,hdop,uptime
```

New Week 4 payload format:

```text
deviceID,fix,latitude,longitude,timestamp_utc,satellites,hdop,uptime,battery_voltage
```

Example:

```text
ASSET-03,1,29.992250,31.555190,2026-05-24T19:53:12Z,5,2.4,807,3.84
```

The receiver forwards the value through MQTT, the backend stores it in Firebase, and the dashboard displays:

```text
Battery Voltage
Battery Status
```

## Battery Status Logic

| Battery Voltage | Status |
|---:|---|
| 4.00V and above | GOOD |
| 3.70V to 3.99V | NORMAL |
| 3.40V to 3.69V | LOW |
| Below 3.40V | CRITICAL |

## Observed Result

During testing, the dashboard displayed:

| Asset | Battery Voltage | Battery Status |
|---|---:|---|
| ASSET-03 | 3.84V | NORMAL |

This confirms that the battery voltage field was successfully transmitted through the full system:

```text
Sender → LoRa → Receiver → MQTT → Firebase → Dashboard
```

## Transmission Interval Modes

| Mode | Send Interval | Purpose |
|---|---:|---|
| DEMO_MODE | 3 seconds | Fast demo/testing |
| NORMAL_MODE | 5 seconds | Balanced operation |
| POWER_SAVING_MODE | 15 seconds | Lower transmission frequency |

## Power Behavior Observation

The OLED display was disabled on the sender to reduce unnecessary power usage.

Battery voltage was monitored on the dashboard as a practical power behavior indicator.

## Current Measurement Note

Direct current draw was not measured because a current meter / USB power meter was not available during this stage.

If a current meter becomes available, power can be calculated using:

```text
Power (W) = Voltage (V) × Current (A)
```

Example:

```text
3.7V × 0.12A = 0.444W
```

## Conclusion

Week 4 power behavior was addressed by adding sender battery voltage monitoring, displaying battery status on the dashboard, and documenting the independent battery-powered sender setup.

This supports the final demo requirement because the sender can operate without a laptop COM connection while still transmitting GPS data wirelessly through LoRa.
