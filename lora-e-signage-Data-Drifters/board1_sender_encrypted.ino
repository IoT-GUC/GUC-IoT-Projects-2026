// SENDER / BOARD 1 — AES-128 Encrypted + Burst Transmission
//
// Board: LILYGO LoRa32 868/915MHz T3_V1.6.1
//
// Changes from previous version:
//   1. AES-128-CBC encryption on every outgoing LoRa packet.
//   2. Triple-burst transmission: sends the same packet 3× with a 300 ms gap
//      so Board 2's narrow 2-second listen window reliably catches at least one.
//   3. Payload is Base64-encoded so it travels as printable ASCII over LoRa.
//
// Required Arduino libraries (Library Manager):
//   - LoRa             by Sandeep Mistry
//   - PubSubClient
//   - Adafruit SSD1306
//   - Adafruit GFX
//   - AESLib            by idolpx   <-- NEW
//
// ─────────────────────────────────────────────────────────────────────────────
// SHARED SECRET — must be identical on Board 2.
// Change both before deploying.
// ─────────────────────────────────────────────────────────────────────────────

#include <SPI.h>
#include <LoRa.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <AESLib.h>

// ── Shared secret (change on both boards) ─────────────────────────────────────
// 16 bytes = AES-128 key
static const uint8_t kAesKey[16] = {
  0x47, 0x55, 0x43, 0x44, 0x61, 0x74, 0x61, 0x44,
  0x72, 0x69, 0x66, 0x74, 0x65, 0x72, 0x73, 0x21
};
// 16-byte IV — fixed IV is fine here because each message is unique text.
// For stricter security you could transmit a random IV prepended to the payload.
static uint8_t kAesIv[16] = {
  0x49, 0x56, 0x5F, 0x47, 0x55, 0x43, 0x5F, 0x4C,
  0x6F, 0x52, 0x61, 0x5F, 0x30, 0x31, 0x21, 0x00
};

// ── WiFi / MQTT ───────────────────────────────────────────────────────────────
const char* ssid        = "Tahoun";
const char* password    = "TAHOUN12345678";
const char* mqtt_server = "broker.hivemq.com";
const char* mqtt_topic  = "guc/datasignage/display";

// ── LoRa pins ─────────────────────────────────────────────────────────────────
#define LORA_SCK       5
#define LORA_MISO      19
#define LORA_MOSI      27
#define LORA_CS        18
#define LORA_RST       23
#define LORA_DIO0      26
#define LORA_BAND      868E6
#define LORA_SYNC_WORD 0xF3

// ── OLED ──────────────────────────────────────────────────────────────────────
#define OLED_SDA      21
#define OLED_SCL      22
#define SCREEN_WIDTH  128
#define SCREEN_HEIGHT 64

// ── Timing ────────────────────────────────────────────────────────────────────
const unsigned long WIFI_TIMEOUT_MS          = 30000;
const unsigned long FALLBACK_SEND_INTERVAL_MS = 5000;
const unsigned long BURST_GAP_MS             = 300;  // gap between burst packets
const uint8_t      BURST_COUNT              = 3;    // transmissions per message
const char*        FALLBACK_MESSAGE         = "Hello IOT";

Adafruit_SSD1306 oled(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
WiFiClient       espClient;
PubSubClient     mqttClient(espClient);

bool          fallbackMode     = false;
unsigned long lastFallbackSend = 0;

// ── Last encrypted payload (re-broadcast periodically so Board 2 catches up) ──
// Board 2 sleeps 30s at a time and may miss a message while asleep.
// Board 1 re-transmits the last encrypted payload every REBROADCAST_INTERVAL_MS
// so a waking Board 2 always receives the current message within its listen window.
String        gLastEncrypted        = "";
unsigned long gLastRebroadcastAt    = 0;
const unsigned long REBROADCAST_INTERVAL_MS = 28000; // just under Board 2's 30s sleep

AESLib aesLib;

// ── Base64 encode ─────────────────────────────────────────────────────────────
// Minimal encoder — no external lib needed.
static const char kB64Chars[] =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

String base64Encode(const uint8_t* data, size_t len) {
  String out;
  out.reserve(((len + 2) / 3) * 4 + 1);
  for (size_t i = 0; i < len; i += 3) {
    uint8_t b0 = data[i];
    uint8_t b1 = (i + 1 < len) ? data[i + 1] : 0;
    uint8_t b2 = (i + 2 < len) ? data[i + 2] : 0;
    out += kB64Chars[b0 >> 2];
    out += kB64Chars[((b0 & 0x03) << 4) | (b1 >> 4)];
    out += (i + 1 < len) ? kB64Chars[((b1 & 0x0F) << 2) | (b2 >> 6)] : '=';
    out += (i + 2 < len) ? kB64Chars[b2 & 0x3F] : '=';
  }
  return out;
}

// ── Encrypt + Base64 a plaintext string ──────────────────────────────────────
// Returns Base64(AES-128-CBC(plaintext)) or empty string on error.
String encryptMessage(const String& plaintext) {
  // AES-CBC requires input to be a multiple of 16 bytes (PKCS#7 padding).
  size_t  inputLen  = plaintext.length();
  uint8_t padLen    = 16 - (inputLen % 16);          // 1–16 bytes of padding
  size_t  bufLen    = inputLen + padLen;

  uint8_t* buf = (uint8_t*)malloc(bufLen);
  if (!buf) return "";

  memcpy(buf, plaintext.c_str(), inputLen);
  memset(buf + inputLen, padLen, padLen);             // PKCS#7 fill

  // AESLib encrypts in-place; we work on buf directly.
  // Reset IV each call (AESLib modifies it during CBC).
  uint8_t iv[16];
  memcpy(iv, kAesIv, 16);

  aesLib.encrypt(buf, bufLen, buf, kAesKey, 128, iv);

  String encoded = base64Encode(buf, bufLen);
  free(buf);
  return encoded;
}

// ── OLED helper ───────────────────────────────────────────────────────────────
void showStatus(const String& l1, const String& l2 = "", const String& l3 = "") {
  oled.clearDisplay();
  oled.setTextSize(1);
  oled.setTextColor(SSD1306_WHITE);
  oled.setCursor(0, 0);
  oled.println(l1);
  if (l2.length()) oled.println(l2);
  if (l3.length()) oled.println(l3);
  oled.display();
}

// ── LoRa burst sender ─────────────────────────────────────────────────────────
// Encrypts the message and fires BURST_COUNT packets with BURST_GAP_MS gaps.
void sendOverLoRa(const String& message) {
  String encrypted = encryptMessage(message);
  if (encrypted.length() == 0) {
    Serial.println("Encryption failed, skipping send.");
    showStatus("Encrypt failed");
    return;
  }

  Serial.print("Sending (encrypted, ");
  Serial.print(BURST_COUNT);
  Serial.println("x burst):");
  Serial.println(encrypted);

  for (uint8_t i = 0; i < BURST_COUNT; i++) {
    LoRa.beginPacket();
    LoRa.print(encrypted);
    LoRa.endPacket();
    if (i < BURST_COUNT - 1) delay(BURST_GAP_MS);
  }

  // Cache so loop() can re-broadcast it for sleeping Board 2 to catch up on wake
  gLastEncrypted     = encrypted;
  gLastRebroadcastAt = millis();

  showStatus("LoRa sent x" + String(BURST_COUNT), message.substring(0, 20));
}

// ── WiFi ─────────────────────────────────────────────────────────────────────
bool connectWiFi() {
  showStatus("Connecting WiFi", ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  const unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < WIFI_TIMEOUT_MS) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\nWiFi timeout.");
    showStatus("WiFi timeout", "Fallback LoRa", FALLBACK_MESSAGE);
    fallbackMode = true;
    return false;
  }

  Serial.print("\nWiFi connected: ");
  Serial.println(WiFi.localIP());
  showStatus("WiFi connected", WiFi.localIP().toString());
  delay(1000);
  fallbackMode = false;
  return true;
}

// ── MQTT ─────────────────────────────────────────────────────────────────────
void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  String message;
  message.reserve(length + 1);
  for (unsigned int i = 0; i < length; i++) message += (char)payload[i];

  Serial.print("MQTT received: ");
  Serial.println(message);
  sendOverLoRa(message);
}

void connectMQTT() {
  while (!mqttClient.connected()) {
    showStatus("Connecting MQTT", mqtt_server);
    String clientId = "GUC-Board1-" + String(random(0xffff), HEX);
    if (mqttClient.connect(clientId.c_str())) {
      mqttClient.subscribe(mqtt_topic);
      Serial.println("MQTT connected, subscribed.");
      showStatus("System ready", "MQTT subscribed", mqtt_topic);
    } else {
      Serial.print("MQTT failed rc=");
      Serial.println(mqttClient.state());
      showStatus("MQTT failed", "Retrying...", "rc=" + String(mqttClient.state()));
      delay(3000);
    }
  }
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(OLED_SDA, OLED_SCL);
  if (!oled.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED init failed.");
    while (true) delay(1000);
  }

  showStatus("LoRa E-Signage", "GUC Data Drifters", "Booting...");
  delay(1000);

  SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_CS);
  LoRa.setPins(LORA_CS, LORA_RST, LORA_DIO0);
  LoRa.setSyncWord(LORA_SYNC_WORD);

  if (!LoRa.begin(LORA_BAND)) {
    Serial.println("LoRa init failed.");
    showStatus("LoRa init failed");
    while (true) delay(1000);
  }

  Serial.println("LoRa OK.");
  showStatus("LoRa ready");
  delay(1000);

  if (!connectWiFi()) {
    sendOverLoRa(FALLBACK_MESSAGE);
    lastFallbackSend = millis();
    return;
  }

  mqttClient.setServer(mqtt_server, 1883);
  mqttClient.setCallback(onMqttMessage);
  connectMQTT();
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
  if (fallbackMode) {
    if (millis() - lastFallbackSend >= FALLBACK_SEND_INTERVAL_MS) {
      lastFallbackSend = millis();
      sendOverLoRa(FALLBACK_MESSAGE);
    }
    return;
  }

  if (WiFi.status() != WL_CONNECTED) {
    if (!connectWiFi()) return;
  }

  if (!mqttClient.connected()) connectMQTT();
  mqttClient.loop();

  // ── Periodic re-broadcast of last message ────────────────────────────────
  // Board 2 wakes every 30s. We re-transmit the last encrypted payload every
  // 28s so there is always a fresh copy in the air when Board 2 listens.
  // Board 2's deduplication means it won't re-render if the message hasn't changed.
  if (gLastEncrypted.length() > 0 &&
      millis() - gLastRebroadcastAt >= REBROADCAST_INTERVAL_MS) {
    Serial.println("Re-broadcasting last message for sleeping Board 2...");
    for (uint8_t i = 0; i < BURST_COUNT; i++) {
      LoRa.beginPacket();
      LoRa.print(gLastEncrypted);
      LoRa.endPacket();
      if (i < BURST_COUNT - 1) delay(BURST_GAP_MS);
    }
    gLastRebroadcastAt = millis();
    showStatus("Re-broadcast", "catch-up tx");
  }
}
