# LoRa Receiver Wirings

This document describes the wiring for:

- LoRa Receiver 1 (`DISPLAY_1`)
- LoRa Receiver 2 (`DISPLAY_2`)

Both receivers use the same hardware and wiring:

- LILYGO LoRa32 T3 V1.6.1 ESP32 board
- Onboard LoRa radio
- Waveshare 4.2-inch V2 black-and-white e-paper display

The receivers only differ in their firmware device ID and initial polling
delay.

## Safety Notes

- Connect a suitable 868 MHz antenna before powering or transmitting with the
  LoRa board.
- Power off the board before changing any wiring.
- Use the LILYGO board's `3.3V` output for the e-paper display so its logic
  voltage matches the ESP32.
- Connect all grounds together.

## Receiver 1 Wiring

Upload `arduino/receiver_1/receiver_1.ino` to this board. It identifies itself
as `DISPLAY_1`.

### E-Paper Display

| Waveshare e-paper pin | LILYGO pin | ESP32 GPIO | Purpose |
| --- | --- | --- | --- |
| `VCC` | `3.3V` | - | Display power |
| `GND` | `GND` | - | Common ground |
| `DIN` | `GPIO 15` | 15 | SPI MOSI / display data |
| `CLK` | `GPIO 14` | 14 | SPI clock |
| `CS` | `GPIO 13` | 13 | Display chip select |
| `DC` | `GPIO 2` | 2 | Data/command select |
| `RST` | `GPIO 4` | 4 | Display reset |
| `BUSY` | `GPIO 35` | 35 | Display busy status |

```text
Waveshare 4.2-inch e-paper        LILYGO LoRa32 T3 V1.6.1
--------------------------        -------------------------
VCC  ---------------------------> 3.3V
GND  ---------------------------> GND
DIN  ---------------------------> GPIO 15
CLK  ---------------------------> GPIO 14
CS   ---------------------------> GPIO 13
DC   ---------------------------> GPIO 2
RST  ---------------------------> GPIO 4
BUSY ---------------------------> GPIO 35
```

## Receiver 2 Wiring

Upload `arduino/receiver_2/receiver_2.ino` to this board. It identifies itself
as `DISPLAY_2`.

### E-Paper Display

| Waveshare e-paper pin | LILYGO pin | ESP32 GPIO | Purpose |
| --- | --- | --- | --- |
| `VCC` | `3.3V` | - | Display power |
| `GND` | `GND` | - | Common ground |
| `DIN` | `GPIO 15` | 15 | SPI MOSI / display data |
| `CLK` | `GPIO 14` | 14 | SPI clock |
| `CS` | `GPIO 13` | 13 | Display chip select |
| `DC` | `GPIO 2` | 2 | Data/command select |
| `RST` | `GPIO 4` | 4 | Display reset |
| `BUSY` | `GPIO 35` | 35 | Display busy status |

```text
Waveshare 4.2-inch e-paper        LILYGO LoRa32 T3 V1.6.1
--------------------------        -------------------------
VCC  ---------------------------> 3.3V
GND  ---------------------------> GND
DIN  ---------------------------> GPIO 15
CLK  ---------------------------> GPIO 14
CS   ---------------------------> GPIO 13
DC   ---------------------------> GPIO 2
RST  ---------------------------> GPIO 4
BUSY ---------------------------> GPIO 35
```

## Onboard LoRa Connections

The LoRa radio is integrated into each LILYGO board, so it does not require
external jumper wires. The receiver firmware uses these onboard connections:

| LoRa signal | ESP32 GPIO |
| --- | --- |
| `SCK` | 5 |
| `MISO` | 19 |
| `MOSI` | 27 |
| `CS` / `NSS` | 18 |
| `RESET` | 23 |
| `DIO0` | 26 |

The onboard LED uses GPIO 25.

## Receiver Differences

| Setting | Receiver 1 | Receiver 2 |
| --- | --- | --- |
| Firmware | `arduino/receiver_1/receiver_1.ino` | `arduino/receiver_2/receiver_2.ino` |
| Device ID | `DISPLAY_1` | `DISPLAY_2` |
| First poll delay | 3 seconds | 33 seconds |
| E-paper wiring | Same as above | Same as above |
| LoRa frequency | 868 MHz | 868 MHz |
