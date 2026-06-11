// LILYGO LoRa32 T3 V1.6.1 ThingsBoard-to-LoRa gateway.
// Connects two downstream display devices to ThingsBoard, caches their shared
// attributes, and serves addressed packets when LoRa receivers poll.

#include <SPI.h>
#include <WiFi.h>
#include <LoRa.h>
#define MQTT_MAX_PACKET_SIZE 1024
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "secrets.h"

namespace {
constexpr long kLoraFrequency = 868E6;

constexpr int kLoraSck = 5;    // Internal PCB connection: SPI clock to LoRa radio.
constexpr int kLoraMiso = 19;  // Internal PCB connection: LoRa radio data to ESP32.
constexpr int kLoraMosi = 27;  // Internal PCB connection: ESP32 data to LoRa radio.
constexpr int kLoraCs = 18;    // Internal PCB connection: selects the LoRa radio for SPI.
constexpr int kLoraReset = 23; // Internal PCB connection: resets the LoRa radio.
constexpr int kLoraDio0 = 26;  // Internal PCB connection: LoRa receive/transmit event signal.

constexpr int kLedPin = 25;    // Internal PCB connection: onboard status LED.
constexpr long kBaudRate = 115200;
constexpr unsigned long kWifiTimeoutMs = 30000;
constexpr unsigned long kRequestResponseDelayMs = 100;
constexpr size_t kMaxLoRaPayloadBytes = 250;

constexpr uint16_t kThingsBoardMqttPort = 1883;

const char* kDisplay1 = "DISPLAY_1";
const char* kDisplay2 = "DISPLAY_2";

const char* kGatewayConnectTopic = "v1/gateway/connect";
const char* kGatewayAttributesTopic = "v1/gateway/attributes";
const char* kGatewayTelemetryTopic = "v1/gateway/telemetry";
}

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

struct DisplayState {
  String deviceId;
  String tutorial;
  String course;
  String slot;
  String room;
  String message;
  String priority;
  unsigned long version;
  bool valid;
};

DisplayState display1 = {kDisplay1, "-", "-", "-", "-", "Waiting for update.",
                         "NORMAL", 0, false};
DisplayState display2 = {kDisplay2, "-", "-", "-", "-", "Waiting for update.",
                         "NORMAL", 0, false};

void blinkStatus(unsigned int onMs = 80, unsigned int offMs = 80) {
  digitalWrite(kLedPin, HIGH);
  delay(onMs);
  digitalWrite(kLedPin, LOW);
  delay(offMs);
}

String getPacketField(const String& payload, const String& key) {
  const String prefix = key + "=";
  int start = payload.indexOf(prefix);
  if (start < 0) {
    return "";
  }

  start += prefix.length();
  int end = payload.indexOf('|', start);
  if (end < 0) {
    end = payload.length();
  }
  return payload.substring(start, end);
}

DisplayState* getDisplay(const String& deviceId) {
  if (deviceId == kDisplay1) {
    return &display1;
  }
  if (deviceId == kDisplay2) {
    return &display2;
  }
  return nullptr;
}

bool initLoRa() {
  SPI.begin(kLoraSck, kLoraMiso, kLoraMosi, kLoraCs);
  LoRa.setPins(kLoraCs, kLoraReset, kLoraDio0);
  LoRa.setSyncWord(0x12);
  return LoRa.begin(kLoraFrequency);
}

void sendLoRaPacket(const String& payload) {
  if (payload.length() > kMaxLoRaPayloadBytes) {
    Serial.print("LoRa payload too long, rejected. Length=");
    Serial.println(payload.length());
    return;
  }

  LoRa.beginPacket();
  LoRa.print(payload);
  LoRa.endPacket();
  LoRa.receive();

  Serial.print("LoRa sent: ");
  Serial.println(payload);
  blinkStatus(100, 0);
}

String buildDataPacket(const DisplayState& state, const String& target = "") {
  String packet;
  packet.reserve(240);
  packet += "TYPE=DATA|TARGET=";
  packet += target.length() > 0 ? target : state.deviceId;
  packet += "|PRIORITY=" + state.priority;
  packet += "|TUT=" + state.tutorial;
  packet += "|COURSE=" + state.course;
  packet += "|SLOT=" + state.slot;
  packet += "|ROOM=" + state.room;
  packet += "|MSG=" + state.message;
  packet += "|VERSION=" + String(state.version);
  return packet;
}

void sendDisplayState(const DisplayState& state, const String& target = "") {
  if (!state.valid) {
    Serial.print("No cached state available for ");
    Serial.println(state.deviceId);
    return;
  }
  sendLoRaPacket(buildDataPacket(state, target));
}

bool publishJson(const char* topic, JsonDocument& document) {
  String payload;
  serializeJson(document, payload);
  const bool published = mqttClient.publish(topic, payload.c_str());
  if (!published) {
    Serial.print("MQTT publish failed for topic ");
    Serial.println(topic);
    return false;
  }
  Serial.print("MQTT published: ");
  Serial.println(topic);
  return true;
}

void connectDownstreamDevice(const char* deviceId) {
  StaticJsonDocument<128> document;
  document["device"] = deviceId;
  document["type"] = "default";
  publishJson(kGatewayConnectTopic, document);
  mqttClient.loop();
  delay(150);
}

void publishAckTelemetry(const String& deviceId, unsigned long version, int rssi) {
  DynamicJsonDocument document(384);
  JsonArray readings = document.createNestedArray(deviceId);
  JsonObject reading = readings.createNestedObject();
  JsonObject values = reading.createNestedObject("values");
  values["lastAppliedVersion"] = version;
  values["lastRssi"] = rssi;
  values["status"] = "online";
  publishJson(kGatewayTelemetryTopic, document);
}

void applyAttributes(DisplayState& state, JsonObject attributes) {
  if (attributes.containsKey("tutorial")) state.tutorial = attributes["tutorial"].as<String>();
  if (attributes.containsKey("course")) state.course = attributes["course"].as<String>();
  if (attributes.containsKey("slot")) state.slot = attributes["slot"].as<String>();
  if (attributes.containsKey("room")) state.room = attributes["room"].as<String>();
  if (attributes.containsKey("message")) state.message = attributes["message"].as<String>();
  if (attributes.containsKey("priority")) state.priority = attributes["priority"].as<String>();
  if (attributes.containsKey("version")) state.version = attributes["version"].as<unsigned long>();

  state.valid = state.version > 0;
  Serial.print("Cached ThingsBoard state for ");
  Serial.print(state.deviceId);
  Serial.print(", version=");
  Serial.println(state.version);
}

void onMqttMessage(char* topic, byte* payloadBytes, unsigned int length) {
  DynamicJsonDocument document(1024);
  const DeserializationError error = deserializeJson(document, payloadBytes, length);
  if (error) {
    Serial.print("Invalid ThingsBoard JSON: ");
    Serial.println(error.c_str());
    return;
  }

  const String deviceId = document["device"] | "";
  DisplayState* state = getDisplay(deviceId);
  if (state == nullptr) {
    Serial.print("Ignoring attributes for unknown device: ");
    Serial.println(deviceId);
    return;
  }

  JsonObject attributes;
  if (String(topic) == kGatewayAttributesTopic) {
    attributes = document["data"].as<JsonObject>();
  }

  if (attributes.isNull()) {
    Serial.println("ThingsBoard message did not contain attributes.");
    return;
  }
  applyAttributes(*state, attributes);
}

void handleLoRaPacket() {
  const int packetSize = LoRa.parsePacket();
  if (packetSize <= 0) {
    return;
  }

  String payload;
  while (LoRa.available()) {
    payload += static_cast<char>(LoRa.read());
  }
  LoRa.receive();

  Serial.print("LoRa received: ");
  Serial.println(payload);

  const String type = getPacketField(payload, "TYPE");
  const String source = getPacketField(payload, "SOURCE");
  DisplayState* state = getDisplay(source);
  if (state == nullptr) {
    Serial.println("Ignoring packet from unknown receiver.");
    return;
  }

  if (type == "REQ") {
    delay(kRequestResponseDelayMs);
    sendDisplayState(*state);
    return;
  }

  if (type == "ACK") {
    const unsigned long version = getPacketField(payload, "VERSION").toInt();
    const int rssi = getPacketField(payload, "RSSI").toInt();
    Serial.print("ACK from ");
    Serial.print(source);
    Serial.print(", version=");
    Serial.println(version);
    if (mqttClient.connected()) {
      publishAckTelemetry(source, version, rssi);
    }
  }
}

const char* wifiStatusName(wl_status_t status) {
  switch (status) {
    case WL_IDLE_STATUS: return "WL_IDLE_STATUS";
    case WL_NO_SSID_AVAIL: return "WL_NO_SSID_AVAIL";
    case WL_SCAN_COMPLETED: return "WL_SCAN_COMPLETED";
    case WL_CONNECTED: return "WL_CONNECTED";
    case WL_CONNECT_FAILED: return "WL_CONNECT_FAILED";
    case WL_CONNECTION_LOST: return "WL_CONNECTION_LOST";
    case WL_DISCONNECTED: return "WL_DISCONNECTED";
    default: return "UNKNOWN";
  }
}

bool connectWiFi() {
  Serial.print("Connecting to WiFi SSID: ");
  Serial.println(kWifiSsid);

  WiFi.disconnect(true);
  delay(300);
  WiFi.mode(WIFI_STA);
  WiFi.begin(kWifiSsid, kWifiPassword);

  const unsigned long startedAt = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startedAt < kWifiTimeoutMs) {
    Serial.print(".");
    blinkStatus();
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi connected. IP=");
    Serial.println(WiFi.localIP());
    return true;
  }

  Serial.print("WiFi connection failed: ");
  Serial.println(wifiStatusName(WiFi.status()));
  return false;
}

bool connectMqtt() {
  const String clientId = "guc-lora-gateway-" + String(random(0xffff), HEX);
  Serial.print("Connecting to ThingsBoard as ");
  Serial.println(clientId);

  if (!mqttClient.connect(clientId.c_str(), kGatewayAccessToken, nullptr)) {
    Serial.print("ThingsBoard MQTT failed, rc=");
    Serial.println(mqttClient.state());
    return false;
  }

  Serial.print("Subscribe shared updates: ");
  Serial.println(mqttClient.subscribe(kGatewayAttributesTopic) ? "OK" : "FAILED");
  Serial.println("ThingsBoard MQTT connected.");
  return true;
}

void initializeDownstreamDevices() {
  connectDownstreamDevice(kDisplay1);
  connectDownstreamDevice(kDisplay2);
  Serial.println("Downstream displays connected. Waiting for shared-attribute pushes.");
}

void setup() {
  pinMode(kLedPin, OUTPUT);
  digitalWrite(kLedPin, LOW);

  Serial.begin(kBaudRate);
  delay(1000);
  randomSeed(micros());

  Serial.println();
  Serial.println("GUC ThingsBoard-to-LoRa gateway");
  Serial.println("Initializing LoRa...");

  if (!initLoRa()) {
    Serial.println("LoRa init failed.");
    while (true) {
      blinkStatus(150, 150);
    }
  }
  Serial.println("LoRa init OK.");
  LoRa.receive();

  mqttClient.setServer(kThingsBoardHost, kThingsBoardMqttPort);
  mqttClient.setCallback(onMqttMessage);
  mqttClient.setKeepAlive(30);
  mqttClient.setSocketTimeout(10);
  mqttClient.setBufferSize(1024);

  connectWiFi();
  if (WiFi.status() == WL_CONNECTED) {
    if (connectMqtt()) {
      initializeDownstreamDevices();
    }
  }
}

void loop() {
  handleLoRaPacket();

  if (WiFi.status() != WL_CONNECTED) {
    if (!connectWiFi()) {
      delay(3000);
      return;
    }
  }

  if (!mqttClient.connected()) {
    Serial.print("ThingsBoard MQTT disconnected, state=");
    Serial.println(mqttClient.state());
    if (!connectMqtt()) {
      delay(3000);
      return;
    }
    initializeDownstreamDevices();
  }

  mqttClient.loop();
}
