// LILYGO LoRa32 T3 V1.6.1 low-power e-paper receiver for DISPLAY_1.

#include <SPI.h>
#include <LoRa.h>
#include <GxEPD2_BW.h>
#include <Fonts/FreeMonoBold18pt7b.h>
#include <Fonts/FreeMonoBold24pt7b.h>
#include <Fonts/FreeMonoBold12pt7b.h>
#include <Fonts/FreeMono9pt7b.h>

// Configuration

namespace {
const char* kDeviceId = "DISPLAY_1";

constexpr long kLoraFrequency = 868E6;
constexpr int kLoraSck = 5;    // Internal PCB connection: SPI clock to LoRa radio.
constexpr int kLoraMiso = 19;  // Internal PCB connection: LoRa radio data to ESP32.
constexpr int kLoraMosi = 27;  // Internal PCB connection: ESP32 data to LoRa radio.
constexpr int kLoraCs = 18;    // Internal PCB connection: selects the LoRa radio for SPI.
constexpr int kLoraReset = 23; // Internal PCB connection: resets the LoRa radio.
constexpr int kLoraDio0 = 26;  // Internal PCB connection: LoRa receive/transmit event signal.

constexpr int kLedPin = 25;    // Internal PCB connection: onboard status LED.
constexpr long kBaudRate = 115200;
constexpr unsigned long kRequestIntervalMs = 60000;
constexpr unsigned long kResponseTimeoutMs = 3000;
constexpr unsigned long kInitialPollDelayMs = 3000;

constexpr int kEpdSck = 14;   // External wire: SPI clock to e-paper display.
constexpr int kEpdMosi = 15;  // External wire: ESP32 data to e-paper display.
constexpr int kEpdCs = 13;    // External wire: selects the e-paper display for SPI.
constexpr int kEpdDc = 2;     // External wire: selects e-paper command or data mode.
constexpr int kEpdReset = 4;  // External wire: resets the e-paper controller.
constexpr int kEpdBusy = 35;  // External wire: e-paper signals when an operation is busy.
}

GxEPD2_BW<GxEPD2_420_GDEY042T81, GxEPD2_420_GDEY042T81::HEIGHT> display(
    GxEPD2_420_GDEY042T81(kEpdCs, kEpdDc, kEpdReset, kEpdBusy));
SPIClass epdSpi(HSPI);

struct Announcement {
  String priority;
  String tutorialNumber;
  String course;
  String slot;
  String room;
  String message;
  unsigned long version;
};

unsigned long lastAppliedVersion = 0;
unsigned long nextPollAt = 0;

// Packet handling

String getPacketField(const String& payload, const String& key) {
  const String prefix = key + "=";
  int start = payload.indexOf(prefix);
  if (start < 0) return "";

  start += prefix.length();
  int end = payload.indexOf('|', start);
  if (end < 0) end = payload.length();
  return payload.substring(start, end);
}

Announcement parseAnnouncement(const String& payload) {
  Announcement announcement;
  announcement.priority = getPacketField(payload, "PRIORITY");
  announcement.tutorialNumber = getPacketField(payload, "TUT");
  announcement.course = getPacketField(payload, "COURSE");
  announcement.slot = getPacketField(payload, "SLOT");
  announcement.room = getPacketField(payload, "ROOM");
  announcement.message = getPacketField(payload, "MSG");
  announcement.version = getPacketField(payload, "VERSION").toInt();

  if (announcement.priority.length() == 0) announcement.priority = "NORMAL";
  if (announcement.tutorialNumber.length() == 0) announcement.tutorialNumber = "-";
  if (announcement.course.length() == 0) announcement.course = "-";
  if (announcement.slot.length() == 0) announcement.slot = "-";
  if (announcement.room.length() == 0) announcement.room = "-";
  if (announcement.message.length() == 0) announcement.message = "No message.";
  return announcement;
}

void sendLoRaPacket(const String& payload) {
  LoRa.beginPacket();
  LoRa.print(payload);
  LoRa.endPacket();
  Serial.print("LoRa sent: ");
  Serial.println(payload);
}

void requestCurrentState() {
  String packet = "TYPE=REQ|SOURCE=";
  packet += kDeviceId;
  packet += "|VERSION=";
  packet += lastAppliedVersion;
  sendLoRaPacket(packet);
}

void sendAck(unsigned long version, int rssi) {
  String packet = "TYPE=ACK|SOURCE=";
  packet += kDeviceId;
  packet += "|VERSION=";
  packet += version;
  packet += "|RSSI=";
  packet += rssi;
  sendLoRaPacket(packet);
}

// Display rendering

bool isEmergency(const Announcement& announcement) {
  String priority = announcement.priority;
  priority.toUpperCase();
  return priority == "EMERGENCY";
}

void drawWrappedText(const String& text, int16_t x, int16_t y, int16_t maxWidth,
                     int16_t lineHeight) {
  String line;
  int16_t cursorY = y;
  int index = 0;

  while (index < text.length()) {
    int nextSpace = text.indexOf(' ', index);
    if (nextSpace < 0) nextSpace = text.length();

    const String word = text.substring(index, nextSpace);
    const String candidate = line.length() == 0 ? word : line + " " + word;
    int16_t boundsX;
    int16_t boundsY;
    uint16_t boundsW;
    uint16_t boundsH;
    display.getTextBounds(candidate, x, cursorY, &boundsX, &boundsY, &boundsW, &boundsH);

    if (boundsW > maxWidth && line.length() > 0) {
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
  }
}

void drawGucMark() {
  display.drawRoundRect(305, 12, 76, 42, 6, GxEPD_BLACK);
  display.fillRect(305, 42, 76, 12, GxEPD_BLACK);
  display.setTextColor(GxEPD_BLACK);
  display.setFont(&FreeMonoBold18pt7b);
  display.setCursor(317, 39);
  display.print("GUC");
  display.setTextColor(GxEPD_WHITE);
  display.setFont(&FreeMono9pt7b);
  display.setCursor(318, 52);
  display.print("UPDATE");
  display.setTextColor(GxEPD_BLACK);
}

void drawField(const char* label, const String& value, int16_t x, int16_t y) {
  display.setFont(&FreeMono9pt7b);
  display.setCursor(x, y);
  display.print(label);
  display.setFont(&FreeMonoBold18pt7b);
  display.setCursor(x + 120, y + 5);
  display.print(value);
}

void renderAnnouncement(const Announcement& announcement) {
  display.setRotation(0);
  display.setFullWindow();
  display.firstPage();
  do {
    display.fillScreen(GxEPD_WHITE);
    display.setTextColor(GxEPD_BLACK);
    drawGucMark();
    display.setFont(&FreeMono9pt7b);
    display.setCursor(18, 30);
    display.print("TUTORIAL ROOM UPDATE");
    display.drawFastHLine(18, 62, 364, GxEPD_BLACK);
    drawField("Tutorial:", announcement.tutorialNumber, 18, 94);
    drawField("Course:", announcement.course, 18, 132);
    drawField("Slot:", announcement.slot, 18, 170);
    drawField("Room:", announcement.room, 18, 208);
    display.drawFastHLine(18, 226, 364, GxEPD_BLACK);
    display.setFont(&FreeMonoBold12pt7b);
    drawWrappedText(announcement.message, 18, 262, 360, 24);
  } while (display.nextPage());
  display.hibernate();
}

void renderEmergency(const Announcement& announcement) {
  display.setRotation(0);
  display.setFullWindow();
  display.firstPage();
  do {
    display.fillScreen(GxEPD_BLACK);
    display.setTextColor(GxEPD_WHITE);
    display.drawRoundRect(14, 14, 372, 272, 10, GxEPD_WHITE);
    display.drawRoundRect(22, 22, 356, 256, 8, GxEPD_WHITE);
    display.setFont(&FreeMonoBold24pt7b);
    display.setCursor(62, 72);
    display.print("EMERGENCY");
    display.drawFastHLine(42, 96, 316, GxEPD_WHITE);
    display.setFont(&FreeMonoBold12pt7b);
    drawWrappedText(announcement.message, 38, 138, 326, 28);
    display.drawFastHLine(42, 224, 316, GxEPD_WHITE);
    display.setFont(&FreeMono9pt7b);
    display.setCursor(46, 252);
    display.print("Tutorial ");
    display.print(announcement.tutorialNumber);
    display.print(" | ");
    display.print(announcement.course);
    display.setCursor(46, 272);
    display.print("Slot ");
    display.print(announcement.slot);
    display.print(" | Room ");
    display.print(announcement.room);
  } while (display.nextPage());
  display.hibernate();
}

void renderPacket(const Announcement& announcement) {
  if (isEmergency(announcement)) {
    renderEmergency(announcement);
  } else {
    renderAnnouncement(announcement);
  }
}

bool handleLoRaPacket() {
  const int packetSize = LoRa.parsePacket();
  if (packetSize <= 0) return false;

  String payload;
  while (LoRa.available()) {
    payload += static_cast<char>(LoRa.read());
  }
  const int rssi = LoRa.packetRssi();
  Serial.print("LoRa received: ");
  Serial.println(payload);

  if (getPacketField(payload, "TYPE") != "DATA") return false;

  const String target = getPacketField(payload, "TARGET");
  if (target != kDeviceId && target != "ALL") {
    Serial.println("Packet is for another display; ignored.");
    return false;
  }

  const Announcement announcement = parseAnnouncement(payload);
  if (announcement.version != lastAppliedVersion) {
    renderPacket(announcement);
    lastAppliedVersion = announcement.version;
    Serial.print("Applied version ");
    Serial.println(lastAppliedVersion);
  } else {
    Serial.println("Version already displayed; redraw skipped.");
  }

  sendAck(announcement.version, rssi);
  digitalWrite(kLedPin, HIGH);
  delay(120);
  digitalWrite(kLedPin, LOW);
  return true;
}

// Polling

void pollGateway() {
  Serial.println("LoRa radio wake.");
  LoRa.idle();
  requestCurrentState();
  LoRa.receive();

  const unsigned long listenStartedAt = millis();
  while (millis() - listenStartedAt < kResponseTimeoutMs) {
    if (handleLoRaPacket()) break;
    delay(1);
  }

  LoRa.sleep();
  Serial.println("LoRa radio sleep.");
}

// Setup

void setup() {
  pinMode(kLedPin, OUTPUT);
  digitalWrite(kLedPin, LOW);
  pinMode(kLoraCs, OUTPUT);
  digitalWrite(kLoraCs, HIGH);
  pinMode(kEpdCs, OUTPUT);
  digitalWrite(kEpdCs, HIGH);

  SPI.begin(kLoraSck, kLoraMiso, kLoraMosi, kLoraCs);
  epdSpi.begin(kEpdSck, -1, kEpdMosi, kEpdCs);
  display.epd2.selectSPI(epdSpi, SPISettings(4000000, MSBFIRST, SPI_MODE0));

  Serial.begin(kBaudRate);
  delay(1000);
  Serial.println();
  Serial.print("Low-power LoRa receiver: ");
  Serial.println(kDeviceId);

  display.init(kBaudRate, true, 2, false);
  renderPacket({"NORMAL", "-", "-", "-", "Waiting",
                String("Requesting state for ") + kDeviceId, 0});

  LoRa.setPins(kLoraCs, kLoraReset, kLoraDio0);
  LoRa.setSyncWord(0x12);
  if (!LoRa.begin(kLoraFrequency)) {
    Serial.println("LoRa init failed.");
    while (true) {
      digitalWrite(kLedPin, HIGH);
      delay(150);
      digitalWrite(kLedPin, LOW);
      delay(150);
    }
  }

  LoRa.sleep();
  nextPollAt = millis() + kInitialPollDelayMs;
  Serial.println("LoRa init OK. Radio sleeping until first poll.");
}

// Loop

void loop() {
  if (static_cast<long>(millis() - nextPollAt) >= 0) {
    do {
      nextPollAt += kRequestIntervalMs;
    } while (static_cast<long>(millis() - nextPollAt) >= 0);
    pollGateway();
  }
}
