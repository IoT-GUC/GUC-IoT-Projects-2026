#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ---------------- TTGO LoRa32 LoRa pinout ----------------
#define SCK   5
#define MISO 19
#define MOSI 27
#define SS    18
#define RST   14
#define DIO0  26
#define BAND  868E6

// ---------------- TTGO LoRa32 OLED pinout ----------------
#define OLED_SDA 21
#define OLED_SCL 22
#define OLED_RST -1
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_ADDR 0x3C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RST);

// ---------------- Receiver state ----------------
String lastRaw = "";
int lastRssi = 0;
unsigned long packetCount = 0;
unsigned long lastPacketMs = 0;

String lastDeviceId = "NA";
String lastFix = "NA";
String lastLat = "NA";
String lastLng = "NA";
String lastUtc = "NA";
String lastSats = "NA";
String lastHdop = "NA";
String lastUptime = "NA";

bool splitPayload(const String &payload,
                  String &deviceId,
                  String &fix,
                  String &lat,
                  String &lng,
                  String &utc,
                  String &sats,
                  String &hdop,
                  String &uptime) {
  int p[7];
  p[0] = payload.indexOf(',');
  if (p[0] < 0) return false;

  for (int i = 1; i < 7; i++) {
    p[i] = payload.indexOf(',', p[i - 1] + 1);
    if (p[i] < 0) return false;
  }

  deviceId = payload.substring(0, p[0]);
  fix      = payload.substring(p[0] + 1, p[1]);
  lat      = payload.substring(p[1] + 1, p[2]);
  lng      = payload.substring(p[2] + 1, p[3]);
  utc      = payload.substring(p[3] + 1, p[4]);
  sats     = payload.substring(p[4] + 1, p[5]);
  hdop     = payload.substring(p[5] + 1, p[6]);
  uptime   = payload.substring(p[6] + 1);

  deviceId.trim();
  fix.trim();
  lat.trim();
  lng.trim();
  utc.trim();
  sats.trim();
  hdop.trim();
  uptime.trim();

  return true;
}

void drawStartupScreen() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);

  display.setCursor(0, 0);
  display.println("LoRa Receiver");
  display.println("Device: RX-01");
  display.println();
  display.println("Initializing...");
  display.println("Waiting for LoRa");

  display.display();
}

void drawWaitingScreen() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);

  display.setCursor(0, 0);
  display.println("LoRa Receiver");
  display.println("Device: RX-01");
  display.println();
  display.println("Status: READY");
  display.println("Waiting packets...");
  display.print("Packets: ");
  display.println(packetCount);

  display.display();
}

void drawPacketScreen(bool parsed) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);

  display.setCursor(0, 0);
  display.println("LoRa Receiver");

  display.print("Pkt: ");
  display.print(packetCount);
  display.print(" RSSI:");
  display.println(lastRssi);

  if (!parsed) {
    display.println("Parsed: NO");
    display.println("Invalid payload");
    display.display();
    return;
  }

  display.print("ID: ");
  display.println(lastDeviceId);

  display.print("Fix: ");
  display.print(lastFix == "1" ? "OK" : "NO");
  display.print(" Sats:");
  display.println(lastSats);

  display.print("Lat: ");
  display.println(lastLat);

  display.print("Lng: ");
  display.println(lastLng);

  display.print("UTC: ");
  display.println(lastUtc);

  display.display();
}

void setupOled() {
  Wire.begin(OLED_SDA, OLED_SCL);

  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    Serial.println("OLED init failed!");
    while (true) delay(1000);
  }

  drawStartupScreen();
}

void setupLoRa() {
  SPI.begin(SCK, MISO, MOSI, SS);
  LoRa.setPins(SS, RST, DIO0);

  if (!LoRa.begin(BAND)) {
    Serial.println("LoRa init failed!");

    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 0);
    display.println("LoRa Receiver");
    display.println("LoRa init FAILED");
    display.println("Check board/band");
    display.display();

    while (true) delay(1000);
  }

  LoRa.enableCrc();
  Serial.println("LoRa Receiver Initialized");
}

void setup() {
  Serial.begin(115200);
  delay(1500);

  Serial.println("Receiver setup started");

  setupOled();
  setupLoRa();

  drawWaitingScreen();
}

void loop() {
  int packetSize = LoRa.parsePacket();

  if (!packetSize) {
    return;
  }

  String incoming = "";
  while (LoRa.available()) {
    incoming += (char)LoRa.read();
  }

  lastRaw = incoming;
  lastRssi = LoRa.packetRssi();
  packetCount++;
  lastPacketMs = millis();

  String deviceId, fix, lat, lng, utc, sats, hdop, uptime;
  bool parsed = splitPayload(incoming, deviceId, fix, lat, lng, utc, sats, hdop, uptime);

  Serial.println("----- PACKET -----");
  Serial.print("Raw: ");    Serial.println(lastRaw);
  Serial.print("RSSI: ");   Serial.println(lastRssi);
  Serial.print("Parsed: "); Serial.println(parsed ? "YES" : "NO");

  if (parsed) {
    lastDeviceId = deviceId;
    lastFix = fix;
    lastLat = lat;
    lastLng = lng;
    lastUtc = utc;
    lastSats = sats;
    lastHdop = hdop;
    lastUptime = uptime;

    Serial.print("ID: ");     Serial.println(deviceId);
    Serial.print("Fix: ");    Serial.println(fix);
    Serial.print("Lat: ");    Serial.println(lat);
    Serial.print("Lng: ");    Serial.println(lng);
    Serial.print("UTC: ");    Serial.println(utc);
    Serial.print("Sats: ");   Serial.println(sats);
    Serial.print("HDOP: ");   Serial.println(hdop);
    Serial.print("Uptime: "); Serial.println(uptime);
  }

  Serial.println("------------------");

  drawPacketScreen(parsed);
}
