#include <Arduino.h>
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>

const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* SERVER_HOST = "192.168.1.50";
const uint16_t SERVER_PORT = 8000;
const char* DEVICE_ID = "ROV-3";
const char* DEVICE_TOKEN = "rov-seed-key-123";
const uint32_t SAMPLE_INTERVAL_MS = 1000;

WebSocketsClient webSocket;

float computeDeviationPercentage() {
  // Isolation point for the sensor fusion algorithm.
  // This function is intentionally separated so the actual EM/magnetic/IMU fusion
  // can change without touching the WebSocket transmission layer.
  // Replace the placeholder math with the real on-device sensor fusion.
  float baseline = 12.0f;
  float current = 18.0f + (sin(millis() / 1500.0f) * 10.0f);
  return max(0.0f, current - baseline);
}

void onMessageCallback(WStype_t type, uint8_t* payload, size_t length) {
  switch (type) {
    case WStype_TEXT:
      Serial.printf("Server: %s\n", (char*)payload);
      break;
    default:
      break;
  }
}

void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
}

void connectWebSocket() {
  String url = String("ws://") + SERVER_HOST + ":" + SERVER_PORT + "/ws/ingest/" + DEVICE_ID + "?token=" + DEVICE_TOKEN;
  webSocket.begin(url.c_str());
  webSocket.onEvent(onMessageCallback);
}

void sendReading() {
  StaticJsonDocument<256> doc;
  doc["device_id"] = DEVICE_ID;
  doc["timestamp"] = "2026-09-06T14:32:11Z";
  doc["deviation_percentage"] = computeDeviationPercentage();
  doc["schema_version"] = 1;

  String payload;
  serializeJson(doc, payload);
  webSocket.sendTXT(payload);
  Serial.println("Sent: " + payload);
}

void setup() {
  Serial.begin(115200);
  connectWiFi();
  connectWebSocket();
}

void loop() {
  webSocket.loop();

  static uint32_t lastSend = 0;
  if (millis() - lastSend >= SAMPLE_INTERVAL_MS) {
    sendReading();
    lastSend = millis();
  }
}
