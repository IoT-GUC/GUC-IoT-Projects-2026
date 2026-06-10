/* =========================================================================
 * RECEIVER NODE: LoRa -> WiFi -> Cloud Dashboard
 * =========================================================================
 * GOAL: Catch the long-range LoRa packet, unpack the 120 bytes back into 
 * a 2D array, convert the integers back to decimals, build a JSON string, 
 * and publish it to an MQTT Broker over WiFi.
 */

#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>
#include <WiFi.h>          // Standard library to connect ESP32 to WiFi
#include <PubSubClient.h>  // Very popular library for MQTT messaging
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>


// --- LORA PINOUT ---
// Must match the exact wiring of the Gateway board!
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_SDA 21
#define OLED_SCL 22
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

#define LORA_CS   18
#define LORA_RST  23
#define LORA_IRQ  26
#define SCK        5
#define MISO      19
#define MOSI      27
#define LORA_BAND 868E6

int rxCount = 0;

// --- WIFI & MQTT CREDENTIALS ---
const char* ssid = "aaaa";
const char* password = "hossam12";

// --- THINGSBOARD MQTT SETTINGS ---
const char* mqtt_server = "10.122.219.178"; // Or your custom server IP
const int mqtt_port = 1883;
// const char* mqtt_topic = ""; // Mandatory ThingsBoard topic
// const char* TOKEN = "fgebr9cmx2dd79x4rljb"; // Get this from the TB Web UI

// Create network objects
WiFiClient espClient;           // Handles the raw TCP/IP WiFi connection
PubSubClient client(espClient); // Handles the MQTT protocol on top of WiFi


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

String getField(const String &packet, const String &key) {
  String tag = key + "=";
  int start = packet.indexOf(tag);
  if (start < 0) return "";
  start += tag.length();
  int end = packet.indexOf('|', start);
  if (end < 0) end = packet.length();
  return packet.substring(start, end);
}

// Custom function to handle dropped MQTT connections
void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...\n");
    String clientId = "ALI-module-";
    clientId += String(random(0xffff), HEX);

    if (client.connect(clientId.c_str())) {
      Serial.println("✅ Connected to Broker!\n");
    } else {
      Serial.printf("✗ Failed. State=%d\n", client.state());
      Serial.printf("  Server : %s\n", mqtt_server);
      Serial.printf("  Port   : %d\n", mqtt_port);
      Serial.printf("  WiFi IP: %s\n", WiFi.localIP().toString().c_str());
      Serial.printf("  Gateway: %s\n", WiFi.gatewayIP().toString().c_str());
      delay(2000);
    }
  }
}


void setup() {
  Serial.begin(115200);
  delay(500);
 
  Wire.begin(OLED_SDA, OLED_SCL);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED failed");
    while (1) delay(1000);
  }
  showMessage("LILYGO RX", "Booting...");

  SPI.begin(SCK, MISO, MOSI, LORA_CS);
  LoRa.setPins(LORA_CS, LORA_RST, LORA_IRQ);
  if (!LoRa.begin(LORA_BAND)) {
    Serial.println("LoRa failed");
    showMessage("LILYGO RX", "LoRa FAILED");
    while (1) delay(1000);
  }
  LoRa.setSyncWord(0x12);

  Serial.println("LilyGO RX ready\n");
  showMessage("LILYGO RX", "Waiting...");
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi\n");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); // Wait half a second, print a dot, check again
    Serial.print(".");
  }
  Serial.println("✅ Connected to WiFi\n");

  // 3. Configure the MQTT Client
  client.setServer(mqtt_server, mqtt_port);
}

// unsigned long lastSendTime = 0;
void loop() {
  if (!client.connected()) {
    reconnectMQTT();
    return;
  }
  client.loop();
  // unsigned long now = millis();
  // if (now - lastSendTime >= 3000) {
  //   lastSendTime = now;
  //   char payload[128];
  //   snprintf(payload, sizeof(payload),
  //     "{\"reading\":\"123.4\",\"conf\":\"HIGH\",\"status\":\"OK\",\"rssi\":-65}");
  //   if (client.publish("meters/test_device/data", payload)) {
  //     Serial.println("✓ Test publish OK");
  //   } else {
  //     Serial.println("✗ Test publish failed");
  //   }
  // }

  int packetSize = LoRa.parsePacket();
  if (!packetSize) return;

  String packet = "";
  while (LoRa.available()) {
    packet += (char)LoRa.read();
  }

  int rssi = LoRa.packetRssi();
  rxCount++;

  Serial.print("Received: ");
  Serial.println(packet);
  Serial.print("RSSI: ");
  Serial.println(rssi);

  if (packet.startsWith("METER|")) {
    String reading = getField(packet, "READING");
    String conf = getField(packet, "CONF");
    String status = getField(packet, "STATUS");

    showMessage(
      "METER RX",
      "R: " + reading,
      "C:" + conf + " S:" + status,
      "RSSI:" + String(rssi) + " #" + String(rxCount)
    );

   char payload[128];
    snprintf(payload, sizeof(payload),
      "{\"reading\":\"%s\",\"conf\":\"%s\",\"status\":\"%s\",\"rssi\":%d}",
      reading.c_str(), conf.c_str(), status.c_str(), rssi);
  
  String deviceId = getField(packet, "ID");
  char topic[64];
  snprintf(topic, sizeof(topic), "meters/%s/data", deviceId.c_str());

    if (client.publish(topic, payload)) {
      Serial.printf("✓ Published: %s\n", payload);
    } else {
      Serial.println("✗ Publish failed\n");
    }

  } else {
    showMessage("LILYGO RX", "Unknown packet", packet.substring(0, 18), "RSSI:" + String(rssi));
  }
}


