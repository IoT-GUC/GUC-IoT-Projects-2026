/*
 * =====================================================================
 *  INDOOR ASSET LOCALIZATION — SENDER (Tag / Asset)
 *  Week 3 — cleaned up, no ThingsBoard, device-ID authenticated
 * =====================================================================
 *  Packet format:  ASSET_ID|PKT:N|BAT:V
 *  SyncWord 0xA5   ← must match receiver exactly (rejects other LoRa)
 * =====================================================================
 */

#include <SPI.h>
#include <LoRa.h>

// ── LoRa pins (TTGO / Heltec ESP32 LoRa v2) ──────────────────────────
#define LORA_CS   18
#define LORA_RST  23
#define LORA_IRQ  26
#define SCK        5
#define MISO      19
#define MOSI      27
#define BAND      868E6          // 868 MHz — Europe / Egypt ISM band

// ── Asset identity ────────────────────────────────────────────────────
// Change this string to uniquely identify each tag device.
// The receiver whitelists this exact ID.
const String ASSET_ID = "LAPTOP-001";

// ── Timing ───────────────────────────────────────────────────────────
const unsigned long TX_INTERVAL_MS = 3000;   // send every 3 seconds

// ── State ─────────────────────────────────────────────────────────────
int packetCounter = 0;

// ── Helpers ───────────────────────────────────────────────────────────
float readBatteryVoltage() {
  // ADC on pin 35 (1/2 voltage divider on Heltec boards)
  // If your board has no divider, return 0 and the receiver ignores it.
  int raw = analogRead(35);
  return raw * (3.3f / 4095.0f) * 2.0f;
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  SPI.begin(SCK, MISO, MOSI, LORA_CS);
  LoRa.setPins(LORA_CS, LORA_RST, LORA_IRQ);

  if (!LoRa.begin(BAND)) {
    Serial.println("[ERROR] LoRa init failed — check wiring!");
    while (true);
  }

  // ── LoRa RF parameters ── must match receiver ──────────────────────
  LoRa.setSyncWord(0xA5);          // private network word — rejects foreign packets
  LoRa.setSpreadingFactor(7);      // SF7 → fast update, good for indoors
  LoRa.setSignalBandwidth(125E3);  // 125 kHz
  LoRa.setCodingRate4(5);          // CR 4/5
  LoRa.setTxPower(14);             // 14 dBm — enough for indoor, not too noisy

  Serial.println("=== Asset Tag Ready ===");
  Serial.print("Asset ID : "); Serial.println(ASSET_ID);
  Serial.print("Interval : "); Serial.print(TX_INTERVAL_MS); Serial.println(" ms");
  Serial.print("Band     : 868 MHz  SW: 0xA5  SF7  BW125  CR4/5  14dBm");
}

void loop() {
  packetCounter++;

  float bat = readBatteryVoltage();

  // ── Packet: "LAPTOP-001|PKT:42|BAT:3.82" ──────────────────────────
  String msg = ASSET_ID
             + "|PKT:" + String(packetCounter)
             + "|BAT:" + String(bat, 2);

  LoRa.beginPacket();
  LoRa.print(msg);
  LoRa.endPacket();

  Serial.print("[TX] "); Serial.println(msg);

  delay(TX_INTERVAL_MS);
}
