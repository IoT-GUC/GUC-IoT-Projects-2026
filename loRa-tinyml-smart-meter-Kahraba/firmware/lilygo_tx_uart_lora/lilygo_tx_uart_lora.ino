/*
  LILYGO TX BOARD: UART FROM ESP32-CAM -> OLED -> LoRa
  ------------------------------------------------------------
  Wiring:
    ESP32-CAM GPIO1 / U0TXD  -> LilyGO CAM_RX
    ESP32-CAM GND            -> LilyGO GND

  This code forwards only packets beginning with METER| so ESP32-CAM debug
  prints do not get forwarded accidentally.
*/

#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>
#include <LoRa.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_SDA 21
#define OLED_SCL 22
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// LoRa pins for common LilyGO LoRa32 boards. Adjust if your exact board differs.
#define LORA_CS   18
#define LORA_RST  23
#define LORA_IRQ  26
#define SCK        5
#define MISO      19
#define MOSI      27
#define LORA_BAND 868E6

// UART from ESP32-CAM.
// If GPIO3/1 conflicts with USB on your LilyGO, choose two free pins and wire accordingly.
#define CAM_RX 3
#define CAM_TX 1

String incomingLine = "";
int sentCount = 0;

void showMessage(String title, String line1, String line2 = "", String line3 = "") {
  
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println(title);
  display.setCursor(0, 16);
  display.println(line1);
  display.setCursor(0, 32);
  display.println(line2);
  display.setCursor(0, 48);
  display.println(line3);
  display.display();
}

void showProcessingScreen(int sentCount) {
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);

  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println("LILYGO TX");

  display.setTextSize(2);
  display.setCursor(0, 18);
  display.println("Processing");

  display.setTextSize(1);
  display.setCursor(0, 44);
  display.println("Running YOLO...");
  display.setCursor(0, 56);
  display.println("Sent: " + String(sentCount));

  display.display();
}

String getField(const String &packet, const String &key) {
  String tag = key + "=";
  int start = packet.indexOf(tag);
  if (start < 0) return "";
  start += tag.length();
  int end = packet.indexOf('|', start);
  if (end < 0) end = packet.length();
  return packet.substring(start, end);
}

void setup() {
  Serial.begin(115200);
  delay(500);

  Wire.begin(OLED_SDA, OLED_SCL);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    while (1) delay(1000);
  }
  showMessage("LILYGO TX", "Booting...");

  SPI.begin(SCK, MISO, MOSI, LORA_CS);
  LoRa.setPins(LORA_CS, LORA_RST, LORA_IRQ);
  if (!LoRa.begin(LORA_BAND)) {
    showMessage("LILYGO TX", "LoRa FAILED");
    while (1) delay(1000);
  }
  LoRa.setSyncWord(0x12);

  Serial2.begin(115200, SERIAL_8N1, CAM_RX, CAM_TX);
  Serial.println("LilyGO TX ready. Waiting for METER packets...");
  showMessage("LILYGO TX", "UART waiting...", "Need METER|...");
}

void forwardPacket(const String &packet) {
  String reading = getField(packet, "READING");
  String conf = getField(packet, "CONF");
  String status = getField(packet, "STATUS");

  LoRa.beginPacket();
  LoRa.print(packet);
  LoRa.endPacket();

  sentCount++;

  Serial.print("Forwarded: ");
  Serial.println(packet);

  if (status == "PROCESSING") {
    showProcessingScreen(sentCount);
    return;
  }

  showMessage(
    "LILYGO TX",
    "R: " + reading + " C:" + conf,
    "S: " + status,
    "Sent: " + String(sentCount)
  );
}

void loop() {
  while (Serial2.available()) {
    char c = Serial2.read();

    if (c == '\n') {
      incomingLine.trim();
      if (incomingLine.length() > 0) {
        Serial.print("UART: ");
        Serial.println(incomingLine);

        if (incomingLine.startsWith("METER|")) {
          forwardPacket(incomingLine);
        }
      }
      incomingLine = "";
    } else if (c != '\r') {
      incomingLine += c;
      if (incomingLine.length() > 180) incomingLine = ""; // safety
    }
  }
}
