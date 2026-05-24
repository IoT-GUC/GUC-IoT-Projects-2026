// RECEIVER / BOARD 2 — AES-128 Encrypted + Deep Sleep (wake 30s / listen 30s)
//
// Board: LILYGO LoRa32 868/915MHz T3_V1.6.1
// Display: Waveshare 4.2 inch e-Paper Module V2, 400×300
//
// Power cycle:
//   1. Wake from deep sleep.
//   2. Init LoRa, listen for the full LISTEN_WINDOW_MS (30 000 ms).
//   3. Any valid encrypted packet → decrypt → render on e-ink.
//      Burst duplicates are deduplicated: same plaintext won't re-render.
//   4. Go back to deep sleep for SLEEP_DURATION_US (30 s).
//   The e-ink display retains its image with zero power while sleeping.
//
// Wiring: unchanged from previous version.
//
// Required Arduino libraries:
//   - LoRa    by Sandeep Mistry
//   - GxEPD2  by Jean-Marc Zingg
//   - Adafruit GFX
//   - AESLib   by idolpx   <-- NEW
//
// ─────────────────────────────────────────────────────────────────────────────
// SHARED SECRET — must be identical to Board 1.
// ─────────────────────────────────────────────────────────────────────────────

#include <SPI.h>
#include <LoRa.h>
#include <GxEPD2_BW.h>
#include <Fonts/FreeMonoBold18pt7b.h>
#include <Fonts/FreeMonoBold12pt7b.h>
#include <Fonts/FreeMono9pt7b.h>
#include <AESLib.h>
#include "esp_sleep.h"

// ── Shared secret (must match Board 1 exactly) ────────────────────────────────
static const uint8_t kAesKey[16] = {
  0x47, 0x55, 0x43, 0x44, 0x61, 0x74, 0x61, 0x44,
  0x72, 0x69, 0x66, 0x74, 0x65, 0x72, 0x73, 0x21
};
static uint8_t kAesIv[16] = {
  0x49, 0x56, 0x5F, 0x47, 0x55, 0x43, 0x5F, 0x4C,
  0x6F, 0x52, 0x61, 0x5F, 0x30, 0x31, 0x21, 0x00
};

// ── Sleep / listen timing ─────────────────────────────────────────────────────
constexpr uint64_t SLEEP_DURATION_US  = 30ULL * 1000ULL * 1000ULL; // 30 seconds
constexpr uint32_t LISTEN_WINDOW_MS   = 30000;  // full 30-second window                       // 2 seconds

// ── Pin / radio constants ─────────────────────────────────────────────────────
namespace {
  constexpr long    kLoraFrequency  = 868E6;
  constexpr int     kLoraSck        = 5;
  constexpr int     kLoraMiso       = 19;
  constexpr int     kLoraMosi       = 27;
  constexpr int     kLoraCs         = 18;
  constexpr int     kLoraReset      = 23;
  constexpr int     kLoraDio0       = 26;
  constexpr int     kLedPin         = 25;
  constexpr long    kBaudRate       = 115200;
  constexpr int     kEpdSck         = 14;
  constexpr int     kEpdMosi        = 15;
  constexpr int     kEpdCs          = 13;
  constexpr int     kEpdDc          = 2;
  constexpr int     kEpdReset       = 4;
  constexpr int     kEpdBusy        = -1;
  constexpr uint8_t kLoraSyncWord   = 0xF3;

  // Layout (400×300 landscape)
  constexpr int kMargin      = 16;
  constexpr int kBadgeX      = 296;
  constexpr int kBadgeY      = 10;
  constexpr int kBadgeW      = 90;
  constexpr int kBadgeH      = 44;
  constexpr int kBadgeRadius = 6;
  constexpr int kHeaderY     = 36;
  constexpr int kDividerY    = 58;
  constexpr int kBodyY       = 90;
  constexpr int kBodyMaxW    = 368;
  constexpr int kLineH       = 28;
  constexpr int kFooterY     = 282;
  constexpr int kFooterRight = 384;

  const char* kWaitMessage       = "Waiting for campus announcement...";
  const char* kPrefix_Emergency  = "EMERGENCY:";
}

// ── Persistent state across sleep cycles (RTC memory) ────────────────────────
// RTC_DATA_ATTR survives deep sleep; normal RAM does not.
RTC_DATA_ATTR int   gMsgCount      = 0;
RTC_DATA_ATTR bool  gHasMessage    = false;   // false = show idle screen on first boot
RTC_DATA_ATTR int   gLastRssi      = 0;
// Store last message in RTC RAM so we can re-render it after sleep if needed.
// 256 chars is plenty for a campus announcement.
RTC_DATA_ATTR char  gLastMessage[256] = {};

// ── Display + SPI ─────────────────────────────────────────────────────────────
GxEPD2_BW<GxEPD2_420_GDEY042T81, GxEPD2_420_GDEY042T81::HEIGHT> display(
    GxEPD2_420_GDEY042T81(kEpdCs, kEpdDc, kEpdReset, kEpdBusy));

SPIClass epdSpi(HSPI);

AESLib aesLib;

// ── Base64 decode ─────────────────────────────────────────────────────────────
static const int8_t kB64Dec[256] = {
  -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
  -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
  -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,62,-1,-1,-1,63,
  52,53,54,55,56,57,58,59,60,61,-1,-1,-1,-1,-1,-1,
  -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,
  15,16,17,18,19,20,21,22,23,24,25,-1,-1,-1,-1,-1,
  -1,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,
  41,42,43,44,45,46,47,48,49,50,51,-1,-1,-1,-1,-1,
  -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
  -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
  -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
  -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
  -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
  -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
  -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
  -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1
};

// Returns decoded length, or 0 on error. Output must be pre-allocated.
size_t base64Decode(const char* input, size_t inputLen, uint8_t* output) {
  size_t outLen = 0;
  for (size_t i = 0; i < inputLen; i += 4) {
    int8_t a = kB64Dec[(uint8_t)input[i]];
    int8_t b = (i+1 < inputLen) ? kB64Dec[(uint8_t)input[i+1]] : 0;
    int8_t c = (i+2 < inputLen && input[i+2] != '=') ? kB64Dec[(uint8_t)input[i+2]] : 0;
    int8_t d = (i+3 < inputLen && input[i+3] != '=') ? kB64Dec[(uint8_t)input[i+3]] : 0;
    if (a < 0 || b < 0) break;
    output[outLen++] = (a << 2) | (b >> 4);
    if (input[i+2] != '=' && i+2 < inputLen) output[outLen++] = ((b & 0x0F) << 4) | (c >> 2);
    if (input[i+3] != '=' && i+3 < inputLen) output[outLen++] = ((c & 0x03) << 6) | d;
  }
  return outLen;
}

// ── Decrypt a Base64-encoded AES-128-CBC payload → plaintext String ───────────
// Returns empty string if decryption or padding validation fails (bad key / interference).
String decryptMessage(const String& encoded) {
  if (encoded.length() == 0 || encoded.length() % 4 != 0) return "";

  size_t maxDecoded = (encoded.length() / 4) * 3 + 4;
  uint8_t* buf = (uint8_t*)malloc(maxDecoded);
  if (!buf) return "";

  size_t decodedLen = base64Decode(encoded.c_str(), encoded.length(), buf);
  if (decodedLen == 0 || decodedLen % 16 != 0) {
    free(buf);
    return "";
  }

  uint8_t iv[16];
  memcpy(iv, kAesIv, 16);

  aesLib.decrypt(buf, decodedLen, buf, kAesKey, 128, iv);

  // Validate and strip PKCS#7 padding
  uint8_t padLen = buf[decodedLen - 1];
  if (padLen == 0 || padLen > 16) {
    free(buf);
    Serial.println("Bad padding — ignoring packet (wrong key or interference).");
    return "";
  }
  for (uint8_t i = 0; i < padLen; i++) {
    if (buf[decodedLen - 1 - i] != padLen) {
      free(buf);
      Serial.println("PKCS#7 mismatch — ignoring packet.");
      return "";
    }
  }

  size_t plaintextLen = decodedLen - padLen;
  String result;
  result.reserve(plaintextLen + 1);
  for (size_t i = 0; i < plaintextLen; i++) result += (char)buf[i];
  free(buf);
  return result;
}

// ── LoRa init ─────────────────────────────────────────────────────────────────
bool initLoRa() {
  LoRa.setPins(kLoraCs, kLoraReset, kLoraDio0);
  LoRa.setSyncWord(kLoraSyncWord);
  return LoRa.begin(kLoraFrequency);
}

// ── Drawing helpers ───────────────────────────────────────────────────────────
void drawRightText(const String& text, int16_t rightEdge, int16_t y) {
  int16_t bx, by; uint16_t bw, bh;
  display.getTextBounds(text, 0, y, &bx, &by, &bw, &bh);
  display.setCursor(rightEdge - bw, y);
  display.print(text);
}

int16_t drawWrappedText(const String& text, int16_t x, int16_t y,
                        int16_t maxWidth, int16_t lineHeight) {
  String line;
  int16_t cursorY = y;
  int     index   = 0;
  while (index <= (int)text.length()) {
    int nextSpace = text.indexOf(' ', index);
    if (nextSpace < 0) nextSpace = text.length();
    String word      = text.substring(index, nextSpace);
    String candidate = (line.length() == 0) ? word : line + " " + word;
    int16_t bx, by; uint16_t bw, bh;
    display.getTextBounds(candidate, x, cursorY, &bx, &by, &bw, &bh);
    if (bw > (uint16_t)maxWidth && line.length() > 0) {
      display.setCursor(x, cursorY);
      display.print(line);
      cursorY += lineHeight;
      line = word;
    } else {
      line = candidate;
    }
    index = nextSpace + 1;
  }
  if (line.length() > 0) {
    display.setCursor(x, cursorY);
    display.print(line);
    cursorY += lineHeight;
  }
  return cursorY;
}

void drawGucBadge(bool isEmergency) {
  if (isEmergency) {
    display.fillRoundRect(kBadgeX, kBadgeY, kBadgeW, kBadgeH, kBadgeRadius, GxEPD_BLACK);
    display.setFont(&FreeMonoBold18pt7b);
    display.setTextColor(GxEPD_WHITE);
    display.setCursor(kBadgeX + 8, kBadgeY + 30);
    display.print("GUC");
    display.setFont(&FreeMono9pt7b);
    display.setCursor(kBadgeX + 8, kBadgeY + 42);
    display.print("! ALERT !");
  } else {
    display.drawRoundRect(kBadgeX, kBadgeY, kBadgeW, kBadgeH, kBadgeRadius, GxEPD_BLACK);
    display.fillRect(kBadgeX, kBadgeY + kBadgeH - 16, kBadgeW, 16, GxEPD_BLACK);
    display.setFont(&FreeMonoBold18pt7b);
    display.setTextColor(GxEPD_BLACK);
    display.setCursor(kBadgeX + 8, kBadgeY + 28);
    display.print("GUC");
    display.setFont(&FreeMono9pt7b);
    display.setTextColor(GxEPD_WHITE);
    display.setCursor(kBadgeX + 10, kBadgeY + 40);
    display.print("UPDATE");
  }
  display.setTextColor(GxEPD_BLACK);
}

// ── Full e-ink render ─────────────────────────────────────────────────────────
void renderMessage(const String& rawMessage, int rssi) {
  bool   isEmergency = rawMessage.startsWith(kPrefix_Emergency);
  String message     = isEmergency
                         ? rawMessage.substring(strlen(kPrefix_Emergency))
                         : rawMessage;
  message.trim();

  display.setRotation(0);
  display.setFullWindow();
  display.firstPage();

  do {
    display.fillScreen(GxEPD_WHITE);
    display.drawFastHLine(0, 0, 400, GxEPD_BLACK);

    display.setFont(&FreeMono9pt7b);
    display.setTextColor(GxEPD_BLACK);
    display.setCursor(kMargin, kHeaderY);
    display.print(isEmergency ? "! EMERGENCY ALERT !" : "CAMPUS ANNOUNCEMENT");

    drawGucBadge(isEmergency);
    display.drawFastHLine(kMargin, kDividerY, 400 - kMargin * 2, GxEPD_BLACK);

    display.setFont(&FreeMonoBold12pt7b);
    display.setTextColor(GxEPD_BLACK);
    drawWrappedText(message, kMargin, kBodyY, kBodyMaxW, kLineH);

    display.drawFastHLine(kMargin, kFooterY - 14, 400 - kMargin * 2, GxEPD_BLACK);
    display.setFont(&FreeMono9pt7b);
    display.setTextColor(GxEPD_BLACK);

    if (rssi != 0) {
      display.setCursor(kMargin, kFooterY);
      display.print("RSSI: " + String(rssi) + " dBm");
    }
    drawRightText("#" + String(gMsgCount), kFooterRight, kFooterY);

  } while (display.nextPage());

  display.hibernate();  // display holds image; draws zero power
}

// ── Setup (runs every wake cycle) ────────────────────────────────────────────
void setup() {
  pinMode(kLedPin,  OUTPUT); digitalWrite(kLedPin,  LOW);
  pinMode(kLoraCs,  OUTPUT); digitalWrite(kLoraCs,  HIGH);
  pinMode(kEpdCs,   OUTPUT); digitalWrite(kEpdCs,   HIGH);

  SPI.begin(kLoraSck, kLoraMiso, kLoraMosi, kLoraCs);
  epdSpi.begin(kEpdSck, -1, kEpdMosi, kEpdCs);
  display.epd2.selectSPI(epdSpi, SPISettings(4000000, MSBFIRST, SPI_MODE0));

  Serial.begin(kBaudRate);
  delay(300);  // shorter boot delay — we're on a tight power budget

  esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
  bool isFirstBoot = (cause != ESP_SLEEP_WAKEUP_TIMER);

  Serial.println(isFirstBoot ? "First boot." : "Woke from deep sleep.");

  // Init display only on first boot OR if we have no stored message yet.
  if (isFirstBoot && !gHasMessage) {
    display.init(kBaudRate, true, 2, false);
    renderMessage(kWaitMessage, 0);
  } else {
    // Re-init display in quiet mode (no full reset flash).
    display.init(kBaudRate, false, 2, false);
  }

  // ── LoRa init ─────────────────────────────────────────────────────────────
  Serial.println("Initializing LoRa...");
  if (!initLoRa()) {
    Serial.println("LoRa init failed — sleeping anyway.");
    goto sleep;
  }
  Serial.println("LoRa OK. Listening for " + String(LISTEN_WINDOW_MS) + " ms...");

  {
    // ── Listen window ────────────────────────────────────────────────────────
    const uint32_t listenStart  = millis();
    bool           gotPacket    = false;
    // Track the last rendered plaintext this cycle to deduplicate burst packets.
    // Board 1 sends 3× the same encrypted payload; we render only the first,
    // then keep listening in case a *different* message arrives later.
    String         lastRendered = "";

    while (millis() - listenStart < LISTEN_WINDOW_MS) {
      int packetSize = LoRa.parsePacket();
      if (packetSize <= 0) { delay(10); continue; }

      // Read raw payload
      String encoded;
      encoded.reserve(packetSize);
      while (LoRa.available()) encoded += (char)LoRa.read();

      const int rssi = LoRa.packetRssi();
      Serial.print("Packet [RSSI ");
      Serial.print(rssi);
      Serial.print("] raw: ");
      Serial.println(encoded);

      // Decrypt — silently drop foreign / corrupted packets
      String plaintext = decryptMessage(encoded);
      if (plaintext.length() == 0) {
        Serial.println("Decryption failed — foreign board or interference, ignoring.");
        continue;
      }

      Serial.print("Decrypted: ");
      Serial.println(plaintext);

      // Deduplicate: if this is a burst repeat of what we just rendered, skip render
      if (plaintext == lastRendered) {
        Serial.println("Duplicate burst packet — skipping re-render.");
        continue;
      }

      // New message — update persistent state and render
      gMsgCount++;
      gLastRssi   = rssi;
      gHasMessage = true;
      strncpy(gLastMessage, plaintext.c_str(), sizeof(gLastMessage) - 1);
      gLastMessage[sizeof(gLastMessage) - 1] = '\0';
      lastRendered = plaintext;

      renderMessage(plaintext, rssi);

      digitalWrite(kLedPin, HIGH); delay(120); digitalWrite(kLedPin, LOW);

      gotPacket = true;
      // Do NOT break — keep listening the full window for follow-up messages
    }

    if (!gotPacket) Serial.println("Nothing received this cycle.");
  }

sleep:
  LoRa.sleep();  // put LoRa radio into sleep mode before ESP32 deep sleep
  Serial.println("Going to deep sleep for 30 s...");
  Serial.flush();

  esp_sleep_enable_timer_wakeup(SLEEP_DURATION_US);
  esp_deep_sleep_start();
  // Never returns — next execution starts at setup() again.
}

// loop() is never reached because setup() ends with deep sleep.
void loop() {}
