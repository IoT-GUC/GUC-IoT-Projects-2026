#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// =======================================================
// WiFi Configuration
// =======================================================
// Change these before uploading
const char* WIFI_SSID = "Adam2";
const char* WIFI_PASSWORD = "Adam2003";

// =======================================================
// MQTT Configuration
// =======================================================
// Public broker for testing.
// For final demo, you can keep this or use your own broker.
const char* MQTT_SERVER = "broker.hivemq.com";
const int MQTT_PORT = 1883;

const char* MQTT_CLIENT_ID = "iot-innovators-receiver01";

const char* MQTT_TOPIC_ALL = "iot-innovators/assets/all";
const char* MQTT_TOPIC_STATUS = "iot-innovators/gateway/status";
const char* MQTT_TOPIC_DEBUG = "iot-innovators/gateway/debug";

// =======================================================
// LoRa Configuration - TTGO LoRa32 Pins
// =======================================================
#define LORA_SCK   5
#define LORA_MISO 19
#define LORA_MOSI 27
#define LORA_SS   18
#define LORA_RST  14
#define LORA_DIO0 26

// Make sure this matches the sender frequency
#define LORA_BAND 868E6

// =======================================================
// Global Objects
// =======================================================
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// =======================================================
// Payload Variables
// =======================================================
unsigned long packetCount = 0;
unsigned long lastPacketTime = 0;

// =======================================================
// Function: Connect to WiFi
// =======================================================
void connectWiFi() {
  Serial.println();
  Serial.println("Connecting to WiFi...");
  Serial.print("SSID: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    attempts++;

    if (attempts > 60) {
      Serial.println();
      Serial.println("WiFi connection failed. Restarting...");
      ESP.restart();
    }
  }

  Serial.println();
  Serial.println("WiFi connected successfully.");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

// =======================================================
// Function: Connect/Reconnect to MQTT
// =======================================================
void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connecting to MQTT broker... ");

    if (mqttClient.connect(MQTT_CLIENT_ID)) {
      Serial.println("connected.");

      mqttClient.publish(
        MQTT_TOPIC_STATUS,
        "receiver01 online",
        true
      );

      Serial.println("Gateway status published.");
    } else {
      Serial.print("failed. MQTT state = ");
      Serial.println(mqttClient.state());
      Serial.println("Retrying in 3 seconds...");
      delay(3000);
    }
  }
}

// =======================================================
// Function: Initialize LoRa
// =======================================================
void setupLoRa() {
  Serial.println("Initializing LoRa receiver...");

  SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_SS);
  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);

  if (!LoRa.begin(LORA_BAND)) {
    Serial.println("LoRa initialization failed.");
    Serial.println("Check LoRa pins, antenna, and frequency.");
    while (true) {
      delay(1000);
    }
  }

  LoRa.enableCrc();

  Serial.println("LoRa receiver initialized successfully.");
  Serial.print("LoRa frequency: ");
  Serial.println(LORA_BAND);
}

// =======================================================
// Function: Split CSV Payload
// Expected payload:
// deviceID,fix,latitude,longitude,timestamp_utc,satellites,hdop,uptime
// =======================================================
bool splitPayload(
  const String& payload,
  String& deviceID,
  String& fix,
  String& latitude,
  String& longitude,
  String& timestampUTC,
  String& satellites,
  String& hdop,
  String& uptime
) {
  int commaPositions[7];

  commaPositions[0] = payload.indexOf(',');
  if (commaPositions[0] == -1) return false;

  for (int i = 1; i < 7; i++) {
    commaPositions[i] = payload.indexOf(',', commaPositions[i - 1] + 1);
    if (commaPositions[i] == -1) return false;
  }

  deviceID     = payload.substring(0, commaPositions[0]);
  fix          = payload.substring(commaPositions[0] + 1, commaPositions[1]);
  latitude     = payload.substring(commaPositions[1] + 1, commaPositions[2]);
  longitude    = payload.substring(commaPositions[2] + 1, commaPositions[3]);
  timestampUTC = payload.substring(commaPositions[3] + 1, commaPositions[4]);
  satellites   = payload.substring(commaPositions[4] + 1, commaPositions[5]);
  hdop         = payload.substring(commaPositions[5] + 1, commaPositions[6]);
  uptime       = payload.substring(commaPositions[6] + 1);

  deviceID.trim();
  fix.trim();
  latitude.trim();
  longitude.trim();
  timestampUTC.trim();
  satellites.trim();
  hdop.trim();
  uptime.trim();

  if (deviceID.length() == 0) return false;

  return true;
}

// =======================================================
// Function: Publish Parsed LoRa Packet to MQTT
// =======================================================
bool publishLocationToMQTT(
  String deviceID,
  String fix,
  String latitude,
  String longitude,
  String timestampUTC,
  String satellites,
  String hdop,
  String uptime,
  int rssi,
  String rawPayload
) {
  StaticJsonDocument<512> doc;

  doc["deviceID"] = deviceID;
  doc["fix"] = fix.toInt();
  doc["latitude"] = latitude.toFloat();
  doc["longitude"] = longitude.toFloat();
  doc["timestamp_utc"] = timestampUTC;
  doc["satellites"] = satellites.toInt();
  doc["hdop"] = hdop.toFloat();
  doc["uptime"] = uptime.toInt();
  doc["rssi"] = rssi;
  doc["gateway"] = "receiver01";
  doc["packet_count"] = packetCount;
  doc["raw_payload"] = rawPayload;

  char jsonBuffer[512];
  size_t jsonSize = serializeJson(doc, jsonBuffer);

  if (jsonSize == 0) {
    Serial.println("Failed to create JSON payload.");
    return false;
  }

  String assetTopic = "iot-innovators/assets/";
  assetTopic += deviceID;
  assetTopic += "/location";

  bool publishedToAll = mqttClient.publish(MQTT_TOPIC_ALL, jsonBuffer);
  bool publishedToAsset = mqttClient.publish(assetTopic.c_str(), jsonBuffer);

  Serial.println("MQTT JSON Payload:");
  Serial.println(jsonBuffer);

  if (publishedToAll && publishedToAsset) {
    Serial.println("MQTT publish successful.");
    Serial.print("Published to: ");
    Serial.println(MQTT_TOPIC_ALL);
    Serial.print("Published to: ");
    Serial.println(assetTopic);
    return true;
  } else {
    Serial.println("MQTT publish failed.");
    return false;
  }
}

// =======================================================
// Setup
// =======================================================
void setup() {
  Serial.begin(115200);
  delay(1500);

  Serial.println();
  Serial.println("====================================");
  Serial.println("IoT Innovators LoRa MQTT Receiver");
  Serial.println("Device: receiver01");
  Serial.println("Mode: LoRa to WiFi/MQTT Gateway");
  Serial.println("OLED: Disabled to reduce power usage");
  Serial.println("====================================");

  connectWiFi();

  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setBufferSize(512);

  reconnectMQTT();

  setupLoRa();

  Serial.println("Receiver is ready.");
  Serial.println("Waiting for LoRa packets...");
}

// =======================================================
// Main Loop
// =======================================================
void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected. Reconnecting...");
    connectWiFi();
  }

  if (!mqttClient.connected()) {
    reconnectMQTT();
  }

  mqttClient.loop();

  int packetSize = LoRa.parsePacket();

  if (packetSize) {
    String incomingPayload = "";

    while (LoRa.available()) {
      incomingPayload += (char)LoRa.read();
    }

    int rssi = LoRa.packetRssi();
    packetCount++;
    lastPacketTime = millis();

    Serial.println();
    Serial.println("---------- LoRa Packet Received ----------");
    Serial.print("Packet Number: ");
    Serial.println(packetCount);

    Serial.print("Raw Payload: ");
    Serial.println(incomingPayload);

    Serial.print("RSSI: ");
    Serial.println(rssi);

    String deviceID;
    String fix;
    String latitude;
    String longitude;
    String timestampUTC;
    String satellites;
    String hdop;
    String uptime;

    bool parsed = splitPayload(
      incomingPayload,
      deviceID,
      fix,
      latitude,
      longitude,
      timestampUTC,
      satellites,
      hdop,
      uptime
    );

    if (!parsed) {
      Serial.println("Payload parsing failed.");
      mqttClient.publish(MQTT_TOPIC_DEBUG, "Invalid LoRa payload received");
      Serial.println("------------------------------------------");
      return;
    }

    Serial.println("Payload parsed successfully.");
    Serial.print("Device ID: ");
    Serial.println(deviceID);
    Serial.print("Fix: ");
    Serial.println(fix);
    Serial.print("Latitude: ");
    Serial.println(latitude);
    Serial.print("Longitude: ");
    Serial.println(longitude);
    Serial.print("UTC Time: ");
    Serial.println(timestampUTC);
    Serial.print("Satellites: ");
    Serial.println(satellites);
    Serial.print("HDOP: ");
    Serial.println(hdop);
    Serial.print("Uptime: ");
    Serial.println(uptime);

    publishLocationToMQTT(
      deviceID,
      fix,
      latitude,
      longitude,
      timestampUTC,
      satellites,
      hdop,
      uptime,
      rssi,
      incomingPayload
    );

    Serial.println("------------------------------------------");
  }
}