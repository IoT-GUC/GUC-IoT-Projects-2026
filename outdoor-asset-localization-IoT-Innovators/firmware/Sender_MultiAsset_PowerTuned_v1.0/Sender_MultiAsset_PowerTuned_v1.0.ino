#include <Arduino.h>
#include <HardwareSerial.h>
#include <TinyGPS++.h>
#include <SPI.h>
#include <LoRa.h>

// =====================================================
// GPS Configuration
// =====================================================

HardwareSerial GPSSerial(1);
TinyGPSPlus gps;

#define GPS_RX_PIN 34
#define GPS_TX_PIN -1

// =====================================================
// LoRa Configuration
// =====================================================

#define LORA_SS    18
#define LORA_RST   23
#define LORA_DIO0  26
#define LORA_BAND  868E6
#define SCK 5        // Serial Clock: the "metronome" for SPI data transfer
#define MISO 19      // Master In Slave Out: data flowing FROM LoRa TO the microcontroller
#define MOSI 27     
// =====================================================
// Battery Voltage Monitoring Configuration
// =====================================================

/*
  Week 4 power behavior feature:
  The sender reads battery voltage and appends it to the LoRa payload.

  Important:
  Many TTGO/LILYGO LoRa32 boards expose battery voltage through GPIO35.
  If your board does not show a realistic battery voltage, check your exact
  board version and update BATTERY_ADC_PIN if needed.
*/

#define ENABLE_BATTERY_MONITORING true

// Common TTGO LoRa32 battery ADC pin.
// If battery voltage always reads 0 or unrealistic values, this pin may need adjustment.
#define BATTERY_ADC_PIN 35

// ESP32 ADC settings
const float ADC_REFERENCE_VOLTAGE = 3.3;
const float ADC_MAX_VALUE = 4095.0;

// Many TTGO boards use a voltage divider, so the ADC sees about half the battery voltage.
const float BATTERY_VOLTAGE_DIVIDER_RATIO = 2.0;

// Optional calibration factor.
// If multimeter reading differs, adjust this slightly, e.g. 1.05 or 0.95.
const float BATTERY_CALIBRATION_FACTOR = 1.00;

// =====================================================
// Power / Demo Mode Configuration
// =====================================================

// Choose one mode only by uncommenting it.

// Fast demo mode: useful during quick TA demo/testing.
// Sends every 3 seconds.
// #define DEMO_MODE

// Normal mode: balanced behavior.
// Sends every 5 seconds.
#define NORMAL_MODE

// Power saving mode: sends less frequently to save battery.
// Sends every 15 seconds.
// #define POWER_SAVING_MODE

#ifdef DEMO_MODE
const unsigned long SEND_INTERVAL_MS = 3000;
const char* POWER_MODE_NAME = "DEMO_MODE";
#endif

#ifdef NORMAL_MODE
const unsigned long SEND_INTERVAL_MS = 5000;
const char* POWER_MODE_NAME = "NORMAL_MODE";
#endif

#ifdef POWER_SAVING_MODE
const unsigned long SEND_INTERVAL_MS = 15000;
const char* POWER_MODE_NAME = "POWER_SAVING_MODE";
#endif

// Safety check: if no mode is selected, fallback to normal mode.
#ifndef DEMO_MODE
#ifndef NORMAL_MODE
#ifndef POWER_SAVING_MODE
const unsigned long SEND_INTERVAL_MS = 5000;
const char* POWER_MODE_NAME = "NORMAL_MODE_FALLBACK";
#endif
#endif
#endif

// =====================================================
// Multi-Asset Configuration
// =====================================================

// The sender switches between these asset IDs over time.
// This validates multi-asset handling using the real LoRa/MQTT/Firebase pipeline.
const char* ASSET_IDS[] = {
  "ASSET-01",
  "ASSET-02",
  "ASSET-03"
};

const int ASSET_COUNT = sizeof(ASSET_IDS) / sizeof(ASSET_IDS[0]);

// For testing, 30 seconds is clear and fast.
// For final demo, you can change this to 60000 or 120000.
const unsigned long ASSET_SWITCH_INTERVAL_MS = 30000;

// =====================================================
// Runtime Variables
// =====================================================

unsigned long bootMs = 0;
unsigned long lastSendMs = 0;
unsigned long lastGpsStatusMs = 0;
unsigned long txCount = 0;

double lastLat = 0.0;
double lastLng = 0.0;
bool hasLastFix = false;

// =====================================================
// Current Asset ID
// =====================================================

const char* getCurrentAssetId() {
  unsigned long elapsedMs = millis() - bootMs;
  int assetIndex = (elapsedMs / ASSET_SWITCH_INTERVAL_MS) % ASSET_COUNT;
  return ASSET_IDS[assetIndex];
}

// =====================================================
// Battery Voltage Helper
// =====================================================

float readBatteryVoltage() {
  if (!ENABLE_BATTERY_MONITORING) {
    return -1.0;
  }

  const int samples = 20;
  long adcTotal = 0;

  for (int i = 0; i < samples; i++) {
    adcTotal += analogRead(BATTERY_ADC_PIN);
    delay(2);
  }

  float adcAverage = adcTotal / (float)samples;

  float measuredVoltage =
    (adcAverage / ADC_MAX_VALUE) * ADC_REFERENCE_VOLTAGE;

  float batteryVoltage =
    measuredVoltage *
    BATTERY_VOLTAGE_DIVIDER_RATIO *
    BATTERY_CALIBRATION_FACTOR;

  return batteryVoltage;
}

String getBatteryStatus(float batteryVoltage) {
  if (batteryVoltage < 0) {
    return "UNKNOWN";
  }

  if (batteryVoltage >= 4.00) {
    return "GOOD";
  }

  if (batteryVoltage >= 3.70) {
    return "NORMAL";
  }

  if (batteryVoltage >= 3.40) {
    return "LOW";
  }

  return "CRITICAL";
}

// =====================================================
// UTC Timestamp Helper
// =====================================================

String getUtcString() {
  if (gps.date.isValid() && gps.time.isValid()) {
    char buf[25];

    snprintf(
      buf,
      sizeof(buf),
      "%04d-%02d-%02dT%02d:%02d:%02dZ",
      gps.date.year(),
      gps.date.month(),
      gps.date.day(),
      gps.time.hour(),
      gps.time.minute(),
      gps.time.second()
    );

    return String(buf);
  }

  return "NA";
}

// =====================================================
// Payload Builder
// =====================================================

// Old payload format:
// deviceID,fix,latitude,longitude,timestamp_utc,satellites,hdop,uptime

// New Week 4 payload format:
// deviceID,fix,latitude,longitude,timestamp_utc,satellites,hdop,uptime,battery_voltage

String buildPayload(bool &fixValid, int &satCount, float &hdopValue, float &batteryVoltage) {
  fixValid = gps.location.isValid() && gps.location.age() < 5000;

  satCount = gps.satellites.isValid()
               ? gps.satellites.value()
               : 0;

  hdopValue = gps.hdop.isValid()
                ? gps.hdop.hdop()
                : 99.9f;

  if (fixValid) {
    lastLat = gps.location.lat();
    lastLng = gps.location.lng();
    hasLastFix = true;
  }

  batteryVoltage = readBatteryVoltage();

  const char* currentAssetId = getCurrentAssetId();

  String payload = "";

  payload += currentAssetId;
  payload += ",";
  payload += fixValid ? "1" : "0";
  payload += ",";

  if (hasLastFix) {
    payload += String(lastLat, 6);
    payload += ",";
    payload += String(lastLng, 6);
  } else {
    payload += "NA,NA";
  }

  payload += ",";

  if (fixValid) {
    payload += getUtcString();
  } else {
    payload += "NA";
  }

  payload += ",";
  payload += String(satCount);
  payload += ",";
  payload += String(hdopValue, 1);
  payload += ",";
  payload += String((millis() - bootMs) / 1000);
  payload += ",";

  if (batteryVoltage >= 0) {
    payload += String(batteryVoltage, 2);
  } else {
    payload += "NA";
  }

  return payload;
}

// =====================================================
// LoRa Setup
// =====================================================

void setupLoRa() {
  SPI.begin(SCK, MISO, MOSI, LORA_SS);

  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);

  if (!LoRa.begin(LORA_BAND)) {
    Serial.println("LoRa init failed");

    while (true) {
      delay(1000);
    }
  }

  LoRa.enableCrc();

  Serial.println("LoRa init OK");
  Serial.print("LoRa Band: ");
  Serial.println(LORA_BAND);
}

// =====================================================
// GPS / Sender Debug Status
// =====================================================

void printGpsStatus() {
  float batteryVoltage = readBatteryVoltage();
  String batteryStatus = getBatteryStatus(batteryVoltage);

  Serial.println();
  Serial.println("========== GPS / SENDER STATUS ==========");

  Serial.print("Power Mode: ");
  Serial.println(POWER_MODE_NAME);

  Serial.print("Send Interval: ");
  Serial.print(SEND_INTERVAL_MS / 1000);
  Serial.println(" seconds");

  Serial.print("Current Asset ID: ");
  Serial.println(getCurrentAssetId());

  Serial.print("Asset Switch Interval: ");
  Serial.print(ASSET_SWITCH_INTERVAL_MS / 1000);
  Serial.println(" seconds");

  Serial.print("Battery Voltage: ");
  if (batteryVoltage >= 0) {
    Serial.print(batteryVoltage, 2);
    Serial.println(" V");
  } else {
    Serial.println("N/A");
  }

  Serial.print("Battery Status: ");
  Serial.println(batteryStatus);

  Serial.print("GPS chars processed: ");
  Serial.println(gps.charsProcessed());

  Serial.print("GPS sentences with fix: ");
  Serial.println(gps.sentencesWithFix());

  Serial.print("GPS failed checksum: ");
  Serial.println(gps.failedChecksum());

  Serial.print("Location valid: ");
  Serial.println(gps.location.isValid() ? "YES" : "NO");

  Serial.print("Location age: ");
  Serial.print(gps.location.age());
  Serial.println(" ms");

  Serial.print("Satellites: ");
  Serial.println(gps.satellites.isValid() ? gps.satellites.value() : 0);

  Serial.print("HDOP: ");
  Serial.println(gps.hdop.isValid() ? gps.hdop.hdop() : 99.9f);

  Serial.print("UTC Date valid: ");
  Serial.println(gps.date.isValid() ? "YES" : "NO");

  Serial.print("UTC Time valid: ");
  Serial.println(gps.time.isValid() ? "YES" : "NO");

  Serial.print("TX Count: ");
  Serial.println(txCount);

  Serial.println("=========================================");
}

// =====================================================
// Setup
// =====================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  bootMs = millis();

  Serial.println();
  Serial.println("========================================================");
  Serial.println("IoT Innovators - Multi-Asset Power-Tuned Sender");
  Serial.println("Mode: No OLED / Battery Friendly Sender");
  Serial.println("Week 4 Feature: Battery Voltage Monitoring");
  Serial.println("Board: TTGO LoRa32");
  Serial.println("========================================================");

  Serial.print("Power Mode: ");
  Serial.println(POWER_MODE_NAME);

  Serial.print("Send Interval: ");
  Serial.print(SEND_INTERVAL_MS / 1000);
  Serial.println(" seconds");

  Serial.println();
  Serial.println("Configured Asset IDs:");

  for (int i = 0; i < ASSET_COUNT; i++) {
    Serial.print("- ");
    Serial.println(ASSET_IDS[i]);
  }

  Serial.print("Asset switch interval: ");
  Serial.print(ASSET_SWITCH_INTERVAL_MS / 1000);
  Serial.println(" seconds");

  Serial.println();
  Serial.println("Battery Monitoring:");
  Serial.print("Enabled: ");
  Serial.println(ENABLE_BATTERY_MONITORING ? "YES" : "NO");

  Serial.print("Battery ADC Pin: GPIO ");
  Serial.println(BATTERY_ADC_PIN);

  analogReadResolution(12);
  analogSetPinAttenuation(BATTERY_ADC_PIN, ADC_11db);

  float initialBatteryVoltage = readBatteryVoltage();

  Serial.print("Initial Battery Voltage: ");
  if (initialBatteryVoltage >= 0) {
    Serial.print(initialBatteryVoltage, 2);
    Serial.println(" V");
  } else {
    Serial.println("N/A");
  }

  Serial.print("Initial Battery Status: ");
  Serial.println(getBatteryStatus(initialBatteryVoltage));

  Serial.println();
  Serial.println("Initializing GPS...");
  GPSSerial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);

  Serial.println("Initializing LoRa...");
  setupLoRa();

  Serial.println();
  Serial.println("Sender ready.");
  Serial.println("After uploading, disconnect USB and power the board using the 3.7V LiPo battery or a power bank.");
  Serial.println("Waiting for GPS data...");
}

// =====================================================
// Main Loop
// =====================================================

void loop() {
  // Read GPS continuously
  while (GPSSerial.available() > 0) {
    char c = GPSSerial.read();
    gps.encode(c);
  }

  // Send LoRa packet based on selected power mode interval
  if (millis() - lastSendMs >= SEND_INTERVAL_MS) {
    lastSendMs = millis();

    bool fixValid = false;
    int sats = 0;
    float hdopValue = 99.9f;
    float batteryVoltage = -1.0;

    String payload = buildPayload(fixValid, sats, hdopValue, batteryVoltage);

    LoRa.beginPacket();
    LoRa.print(payload);
    LoRa.endPacket();

    txCount++;

    Serial.println();
    Serial.println("------------- LoRa Packet Sent -------------");

    Serial.print("TX Count: ");
    Serial.println(txCount);

    Serial.print("Power Mode: ");
    Serial.println(POWER_MODE_NAME);

    Serial.print("Current Asset ID: ");
    Serial.println(getCurrentAssetId());

    Serial.print("Payload: ");
    Serial.println(payload);

    Serial.print("GPS Fix: ");
    Serial.println(fixValid ? "VALID" : "INVALID");

    if (fixValid) {
      Serial.print("Latitude: ");
      Serial.println(gps.location.lat(), 6);

      Serial.print("Longitude: ");
      Serial.println(gps.location.lng(), 6);

      Serial.print("UTC: ");
      Serial.println(getUtcString());
    } else if (hasLastFix) {
      Serial.println("Using last known coordinates because current GPS fix is invalid.");

      Serial.print("Last Latitude: ");
      Serial.println(lastLat, 6);

      Serial.print("Last Longitude: ");
      Serial.println(lastLng, 6);
    } else {
      Serial.println("No valid GPS fix yet.");
    }

    Serial.print("Satellites: ");
    Serial.println(sats);

    Serial.print("HDOP: ");
    Serial.println(hdopValue, 1);

    Serial.print("Battery Voltage: ");
    if (batteryVoltage >= 0) {
      Serial.print(batteryVoltage, 2);
      Serial.println(" V");
    } else {
      Serial.println("N/A");
    }

    Serial.print("Battery Status: ");
    Serial.println(getBatteryStatus(batteryVoltage));

    Serial.println("--------------------------------------------");
  }

  // Print debug status every 10 seconds while USB Serial is connected
  if (millis() - lastGpsStatusMs >= 10000) {
    lastGpsStatusMs = millis();
    printGpsStatus();
  }
}
