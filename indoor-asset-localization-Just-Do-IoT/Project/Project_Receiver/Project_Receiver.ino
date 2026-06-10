/*
 * =====================================================================
 *  INDOOR ASSET LOCALIZATION — RECEIVER (Gateway / Fixed Node)
 *  Week 3 — cleaned up, no ThingsBoard, device-ID whitelisted
 * =====================================================================
 *  Accepts packets ONLY from ALLOWED_ASSETS list.
 *  Forwards to your local FastAPI backend over WiFi.
 *  SyncWord 0xA5  ← must match sender exactly.
 * =====================================================================
 */

#include <SPI.h>
#include <LoRa.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_GFX.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <time.h>

// ── LoRa pins ─────────────────────────────────────────────────────────
#define SCK       5
#define MISO     19
#define MOSI     27
#define LORA_CS  18
#define LORA_RST 23
#define LORA_IRQ 26
#define BAND     868E6

// ── OLED ──────────────────────────────────────────────────────────────
#define SCREEN_WIDTH  128
#define SCREEN_HEIGHT  64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// ── WiFi credentials — update these ───────────────────────────────────
const char* WIFI_SSID     = "Youssef's iPhone";
const char* WIFI_PASSWORD = "Kheloti1";

// ── Backend URL — use your PC's LAN IP, NOT localhost ─────────────────
// Find it with: ipconfig (Windows) or ip addr (Linux/Mac)
const char* BACKEND_URL = "http://172.20.10.2:8000/telemetry";

// ── Whitelist: only packets from these asset IDs are accepted ─────────
// Add or remove asset IDs to match your registered sender tags.
const String ALLOWED_ASSETS[] = { "LAPTOP-001"};
const int    ALLOWED_COUNT    = 1;

// ── Zone classification (same thresholds as backend) ──────────────────
// The backend also re-computes this; the local copy is only for OLED display.
String getZone(int rssi) {
  if (rssi >= -60)  return "Same Room";
  if (rssi >= -80)  return "Nearby Room";
  if (rssi >= -100) return "Same Floor";
  return                   "Out of Range";
}

// ── Asset ID whitelist check ───────────────────────────────────────────
bool isAllowed(const String& id) {
  for (int i = 0; i < ALLOWED_COUNT; i++) {
    if (ALLOWED_ASSETS[i] == id) return true;
  }
  return false;
}

// ── Parse a field from pipe-delimited packet ──────────────────────────
// Packet format: "LAPTOP-001|PKT:42|BAT:3.82"
String parseField(const String& msg, const String& key) {
  int start = msg.indexOf(key);
  if (start == -1) return "";
  start += key.length();
  int end = msg.indexOf('|', start);
  return (end == -1) ? msg.substring(start) : msg.substring(start, end);
}

// ── NTP wall-clock time ───────────────────────────────────────────────
String getRealTime() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) return "00:00:00";
  char buf[20];
  strftime(buf, sizeof(buf), "%H:%M:%S", &timeinfo);
  return String(buf);
}

// ── Forward to FastAPI backend ────────────────────────────────────────
void sendToBackend(const String& assetID, int rssi, float snr,
                   float bat,   const String& zone, const String& ts) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Not connected — skipping POST");
    return;
  }

  HTTPClient http;
  http.begin(BACKEND_URL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);   // 5-second timeout so we don't block the loop

  // Build JSON manually (avoids pulling in ArduinoJson for a simple payload)
  String payload = "{";
  payload += "\"assetID\":\""   + assetID + "\",";
  payload += "\"rssi\":"        + String(rssi)      + ",";
  payload += "\"snr\":"         + String(snr, 2)    + ",";
  payload += "\"battery\":"     + String(bat, 2)    + ",";
  payload += "\"timestamp\":\"" + ts  + "\"";
  payload += "}";

  int code = http.POST(payload);

  if (code == 200) {
    Serial.println("[POST] OK");
  } else {
    Serial.print("[POST] Error: "); Serial.println(code);
  }
  http.end();
}

// ── OLED helper ───────────────────────────────────────────────────────
void updateOLED(const String& assetID, int rssi, float snr,
                const String& zone,    const String& ts) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);

  display.setCursor(0, 0);  display.println("= ASSET LOCATED =");
  display.setCursor(0, 14); display.print("ID  : "); display.println(assetID);
  display.setCursor(0, 26); display.print("RSSI: "); display.print(rssi); display.println(" dBm");
  display.setCursor(0, 38); display.print("SNR : "); display.print(snr, 1); display.println(" dB");
  display.setCursor(0, 50); display.print("Zone: "); display.println(zone);
  display.setCursor(64, 56); display.print(ts);

  display.display();
}

// ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(1000);

  // OLED init
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("[OLED] Init failed — continuing without display");
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0); display.println("Connecting WiFi...");
  display.display();

  // WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("[WiFi] Connecting");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500); Serial.print("."); attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected → " + WiFi.localIP().toString());
  } else {
    Serial.println("\n[WiFi] FAILED — running offline (OLED only)");
  }

  // NTP — Egypt = UTC+2
  configTime(2 * 3600, 0, "pool.ntp.org", "time.nist.gov");
  delay(2000);

  // LoRa init
  SPI.begin(SCK, MISO, MOSI, LORA_CS);
  LoRa.setPins(LORA_CS, LORA_RST, LORA_IRQ);

  if (!LoRa.begin(BAND)) {
    Serial.println("[LoRa] Init FAILED!");
    display.clearDisplay();
    display.setCursor(0, 0); display.println("LoRa FAILED!");
    display.display();
    while (true);
  }

  // ── RF parameters — must exactly match sender ──────────────────────
  LoRa.setSyncWord(0xA5);          // rejects packets from other LoRa networks
  LoRa.setSpreadingFactor(7);
  LoRa.setSignalBandwidth(125E3);
  LoRa.setCodingRate4(5);

  Serial.println("[LoRa] Ready — listening on 868 MHz  SW:0xA5  SF7");

  display.clearDisplay();
  display.setCursor(0, 0); display.println("Receiver Ready");
  display.setCursor(0, 14); display.print("IP: "); display.println(WiFi.localIP().toString());
  display.display();
}

// ─────────────────────────────────────────────────────────────────────
void loop() {
  int packetSize = LoRa.parsePacket();
  if (packetSize == 0) return;    // nothing received

  // Read raw bytes
  String received = "";
  while (LoRa.available()) received += (char)LoRa.read();

  int   rssi = LoRa.packetRssi();
  float snr  = LoRa.packetSnr();

  // ── Parse asset ID (first field before first '|') ──────────────────
  int pipePos = received.indexOf('|');
  String assetID = (pipePos > 0) ? received.substring(0, pipePos) : received;

  // ── Whitelist check — drop packets from unknown senders ────────────
  if (!isAllowed(assetID)) {
    Serial.print("[IGNORED] Unknown sender: "); Serial.println(assetID);
    return;
  }

  // ── Parse optional battery field ───────────────────────────────────
  String batStr = parseField(received, "BAT:");
  float  bat    = batStr.length() > 0 ? batStr.toFloat() : 0.0f;

  String zone = getZone(rssi);
  String ts   = getRealTime();

  // ── Serial log ─────────────────────────────────────────────────────
  Serial.println("=============================");
  Serial.print("Time     : "); Serial.println(ts);
  Serial.print("Asset    : "); Serial.println(assetID);
  Serial.print("Raw Msg  : "); Serial.println(received);
  Serial.print("RSSI     : "); Serial.print(rssi); Serial.println(" dBm");
  Serial.print("SNR      : "); Serial.print(snr, 1); Serial.println(" dB");
  Serial.print("Battery  : "); Serial.print(bat, 2); Serial.println(" V");
  Serial.print("Zone     : "); Serial.println(zone);
  Serial.println("=============================");

  // ── Send to backend ────────────────────────────────────────────────
  sendToBackend(assetID, rssi, snr, bat, zone, ts);

  // ── Update OLED ────────────────────────────────────────────────────
  updateOLED(assetID, rssi, snr, zone, ts);
}
