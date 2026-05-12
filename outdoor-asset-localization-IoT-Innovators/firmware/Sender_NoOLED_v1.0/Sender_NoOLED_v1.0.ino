#include <Arduino.h>
#include <HardwareSerial.h>
#include <TinyGPS++.h>
#include <SPI.h>
#include <LoRa.h>

// ================= GPS =================
HardwareSerial GPSSerial(1);
TinyGPSPlus gps;

#define GPS_RX_PIN 34
#define GPS_TX_PIN -1

// ================= LoRa =================
#define LORA_SS    18
#define LORA_RST   14
#define LORA_DIO0  26
#define LORA_BAND  868E6

// ================= App =================
const char* DEVICE_ID = "ASSET-01";
const unsigned long SEND_INTERVAL_MS = 5000;

unsigned long lastSendMs = 0;
unsigned long bootMs = 0;
unsigned long txCount = 0;
unsigned long lastGpsStatusMs = 0;

double lastLat = 0.0;
double lastLng = 0.0;
bool hasLastFix = false;

// ================= UTC Time =================
String getUtcString() {
  if (gps.date.isValid() && gps.time.isValid()) {
    char buf[25];
    snprintf(buf, sizeof(buf),
             "%04d-%02d-%02dT%02d:%02d:%02dZ",
             gps.date.year(),
             gps.date.month(),
             gps.date.day(),
             gps.time.hour(),
             gps.time.minute(),
             gps.time.second());
    return String(buf);
  }

  return "NA";
}

// ================= Payload Builder =================
// Payload format:
// deviceID,fix,latitude,longitude,timestamp_utc,satellites,hdop,uptime
String buildPayload(bool &fixValid, int &satCount, float &hdopValue) {
  fixValid = gps.location.isValid() && gps.location.age() < 5000;
  satCount = gps.satellites.isValid() ? gps.satellites.value() : 0;
  hdopValue = gps.hdop.isValid() ? gps.hdop.hdop() : 99.9f;

  if (fixValid) {
    lastLat = gps.location.lat();
    lastLng = gps.location.lng();
    hasLastFix = true;
  }

  String payload = DEVICE_ID;
  payload += ",";
  payload += (fixValid ? "1" : "0");
  payload += ",";

  if (hasLastFix) {
    payload += String(lastLat, 6);
    payload += ",";
    payload += String(lastLng, 6);
  } else {
    payload += "NA,NA";
  }

  payload += ",";
  payload += (fixValid ? getUtcString() : String("NA"));
  payload += ",";
  payload += String(satCount);
  payload += ",";
  payload += String(hdopValue, 1);
  payload += ",";
  payload += String((millis() - bootMs) / 1000);

  return payload;
}

// ================= LoRa Setup =================
void setupLoRa() {
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

// ================= GPS Debug Status =================
void printGpsStatus() {
  Serial.println("----- GPS STATUS -----");
  Serial.print("Chars processed: ");
  Serial.println(gps.charsProcessed());

  Serial.print("Sentences with fix: ");
  Serial.println(gps.sentencesWithFix());

  Serial.print("Failed checksum: ");
  Serial.println(gps.failedChecksum());

  Serial.print("Location valid: ");
  Serial.println(gps.location.isValid() ? "YES" : "NO");

  Serial.print("Satellites: ");
  Serial.println(gps.satellites.isValid() ? gps.satellites.value() : 0);

  Serial.print("HDOP: ");
  Serial.println(gps.hdop.isValid() ? gps.hdop.hdop() : 99.9f);

  Serial.print("Date valid: ");
  Serial.println(gps.date.isValid() ? "YES" : "NO");

  Serial.print("Time valid: ");
  Serial.println(gps.time.isValid() ? "YES" : "NO");

  Serial.print("TX Count: ");
  Serial.println(txCount);

  Serial.println("----------------------");
}

// ================= Setup =================
void setup() {
  Serial.begin(115200);
  delay(1000);

  bootMs = millis();

  Serial.println();
  Serial.println("====================================");
  Serial.println("GPS + LoRa Sender starting...");
  Serial.println("Device: ASSET-01");
  Serial.println("Mode: No OLED / Low-power sender");
  Serial.println("OLED: Disabled to reduce power usage");
  Serial.println("====================================");

  GPSSerial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);

  setupLoRa();

  Serial.println("Waiting for GPS data...");
}

// ================= Main Loop =================
void loop() {
  while (GPSSerial.available() > 0) {
    char c = GPSSerial.read();
    gps.encode(c);
  }

  if (millis() - lastSendMs >= SEND_INTERVAL_MS) {
    lastSendMs = millis();

    bool fixValid = false;
    int sats = 0;
    float hdopValue = 99.9f;

    String payload = buildPayload(fixValid, sats, hdopValue);

    LoRa.beginPacket();
    LoRa.print(payload);
    LoRa.endPacket();

    txCount++;

    Serial.println();
    Serial.println("---------- LoRa Packet Sent ----------");
    Serial.print("TX Count: ");
    Serial.println(txCount);

    Serial.print("Sent Payload: ");
    Serial.println(payload);

    Serial.print("Current Fix: ");
    if (fixValid) {
      Serial.print(gps.location.lat(), 6);
      Serial.print(", ");
      Serial.println(gps.location.lng(), 6);
    } else {
      Serial.println("INVALID");
    }

    Serial.println("--------------------------------------");
  }

  if (millis() - lastGpsStatusMs >= 5000) {
    lastGpsStatusMs = millis();
    printGpsStatus();
  }
}
