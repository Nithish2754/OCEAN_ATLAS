/**
 * oceanatlas_ws_sender.ino – Quick-flash sketch reference for Arduino IDE
 * =========================================================================
 * This top-level .ino mirrors the PlatformIO firmware at:
 *   esp32/OCEAN ATLAS/src/main.cpp
 *
 * For production builds, use PlatformIO (esp32/OCEAN ATLAS/).
 * This file is kept as an Arduino IDE convenience.
 *
 * CONFIGURE BEFORE FLASHING:
 */
#define WIFI_SSID        "SANJAY LAPTOP"       // ← replace
#define WIFI_PASSWORD    "qwertyuiop"    // ← replace
#define SERVER_HOST      "192.168.137.16"       // PC Wi-Fi LAN IP
#define SERVER_PORT      8000
// ──────────────────────────────────────────────────────────────────────────

#include <Arduino.h>
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <LiquidCrystal.h>

// ── Pin definitions ──────────────────────────────────────────────────────────
#define TRIG_PIN     5
#define ECHO_PIN     18
#define METAL_PIN    34

// ── Device credentials ───────────────────────────────────────────────────────
const char* DEVICE_ID    = "ROV-01";
const char* DEVICE_TOKEN = "rov-esp32-key-001";

// ── Intervals (ms) ───────────────────────────────────────────────────────────
const uint32_t SENSOR_INTERVAL    = 100;
const uint32_t TELEMETRY_INTERVAL = 1000;
const uint32_t LCD_INTERVAL       = 1500;

// ── Metal threshold ──────────────────────────────────────────────────────────
const float METAL_THRESHOLD_V = 0.30f;

// ── MPU6050 ──────────────────────────────────────────────────────────────────
#define MPU6050_ADDR 0x68

// ── LCD ──────────────────────────────────────────────────────────────────────
LiquidCrystal lcd(13, 14, 27, 26, 25, 33);

WebSocketsClient webSocket;

float    g_distanceCm   = -1.0f;
float    g_metalVoltage = 0.0f;
bool     g_metalDetected = false;
float    g_accelX = 0.0f, g_accelY = 0.0f, g_accelZ = 1.0f;
bool     g_mpuOk  = false;
bool     wsConnected = false;
bool     lcdScreen2 = false;

uint32_t lastSensor = 0, lastTelemetry = 0, lastLcd = 0;


float readUltrasonic() {
  digitalWrite(TRIG_PIN, LOW);  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long dur = pulseIn(ECHO_PIN, HIGH, 30000UL);
  if (dur == 0) return -1.0f;
  float cm = dur * 0.034f / 2.0f;
  return (cm < 2.0f || cm > 400.0f) ? -1.0f : cm;
}

float readMetalVoltage() {
  int raw = analogRead(METAL_PIN);
  if (raw < 0 || raw > 4095) return 0.0f;
  return (raw / 4095.0f) * 3.3f;
}

bool readMPU6050(float &ax, float &ay, float &az) {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  Wire.requestFrom((uint8_t)MPU6050_ADDR, (uint8_t)6);
  if (Wire.available() < 6) return false;
  int16_t AcX = (Wire.read() << 8) | Wire.read();
  int16_t AcY = (Wire.read() << 8) | Wire.read();
  int16_t AcZ = (Wire.read() << 8) | Wire.read();
  ax = AcX / 16384.0f; ay = AcY / 16384.0f; az = AcZ / 16384.0f;
  return true;
}

void readAllSensors() {
  g_distanceCm   = readUltrasonic();
  g_metalVoltage = readMetalVoltage();
  g_metalDetected = (g_metalVoltage > METAL_THRESHOLD_V);
  float ax, ay, az;
  g_mpuOk = readMPU6050(ax, ay, az);
  if (g_mpuOk) { g_accelX = ax; g_accelY = ay; g_accelZ = az; }
}

void updateLCD() {
  lcd.clear();
  if (!lcdScreen2) {
    lcd.setCursor(0, 0);
    if (g_distanceCm < 0) lcd.print("Dist: No echo");
    else { lcd.print("Dist: "); lcd.print(g_distanceCm, 1); lcd.print(" cm"); }
    lcd.setCursor(0, 1);
    lcd.print(g_metalDetected ? "METAL DETECTED!" : "Metal: Clear");
  } else {
    lcd.setCursor(0, 0);
    if (!g_mpuOk) { lcd.print("MPU: ERROR"); }
    else {
      lcd.print("X:"); lcd.print(g_accelX, 2);
      lcd.print(" Y:"); lcd.print(g_accelY, 2);
      lcd.setCursor(0, 1);
      lcd.print("Z:"); lcd.print(g_accelZ, 2); lcd.print("g");
    }
  }
  lcdScreen2 = !lcdScreen2;
}

void sendTelemetry() {
  if (!wsConnected) return;
  JsonDocument doc;
  doc["device_id"]            = DEVICE_ID;
  doc["schema_version"]       = 1;
  doc["deviation_percentage"] = g_metalVoltage * 30.3f;  // real voltage → legacy field
  doc["metal_detected"]       = g_metalDetected;
  doc["metal_voltage"]        = round(g_metalVoltage * 1000.0f) / 1000.0f;
  doc["distance_cm"]          = (g_distanceCm >= 0) ? (JsonVariant)(round(g_distanceCm * 10.0f) / 10.0f) : nullptr;
  doc["accel_x"]              = g_mpuOk ? (JsonVariant)(round(g_accelX * 1000.0f) / 1000.0f) : nullptr;
  doc["accel_y"]              = g_mpuOk ? (JsonVariant)(round(g_accelY * 1000.0f) / 1000.0f) : nullptr;
  doc["accel_z"]              = g_mpuOk ? (JsonVariant)(round(g_accelZ * 1000.0f) / 1000.0f) : nullptr;
  doc["latitude"]             = nullptr;
  doc["longitude"]            = nullptr;
  String payload; serializeJson(doc, payload);
  webSocket.sendTXT(payload);
  Serial.print("[TX] "); Serial.println(payload);
}

void onWsEvent(WStype_t type, uint8_t* payload, size_t length) {
  if (type == WStype_CONNECTED)    { wsConnected = true;  Serial.println("[WS] Connected"); }
  if (type == WStype_DISCONNECTED) { wsConnected = false; Serial.println("[WS] Disconnected"); }
  if (type == WStype_TEXT)         { Serial.printf("[WS] Server: %s\n", (char*)payload); }
}

void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("[WiFi] Connecting");
  uint32_t t0 = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
    if (millis() - t0 > 30000UL) { ESP.restart(); }
  }
  Serial.printf("\n[WiFi] IP: %s\n", WiFi.localIP().toString().c_str());
}

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT); pinMode(ECHO_PIN, INPUT);
  digitalWrite(TRIG_PIN, LOW);
  analogSetAttenuation(ADC_11db);

  lcd.begin(16, 2);
  lcd.print("Ocean Atlas"); lcd.setCursor(0,1); lcd.print("Starting...");

  Wire.begin(21, 22);
  Wire.beginTransmission(MPU6050_ADDR); Wire.write(0x6B); Wire.write(0x00);
  g_mpuOk = (Wire.endTransmission(true) == 0);
  Serial.printf("[MPU6050] %s\n", g_mpuOk ? "OK" : "FAILED");

  connectWiFi();

  String wsPath = String("/ws/ingest/") + DEVICE_ID + "?token=" + DEVICE_TOKEN;
  webSocket.begin(SERVER_HOST, SERVER_PORT, wsPath);
  webSocket.onEvent(onWsEvent);
  webSocket.setReconnectInterval(3000);

  lcd.clear(); lcd.print("ROV-01 Ready");
  lcd.setCursor(0,1); lcd.print(WiFi.localIP().toString());
}

void loop() {
  uint32_t now = millis();
  webSocket.loop();

  if (WiFi.status() != WL_CONNECTED) connectWiFi();
  if (now - lastSensor    >= SENSOR_INTERVAL)    { readAllSensors();  lastSensor    = now; }
  if (now - lastLcd       >= LCD_INTERVAL)       { updateLCD();       lastLcd       = now; }
  if (now - lastTelemetry >= TELEMETRY_INTERVAL) { sendTelemetry();   lastTelemetry = now; }
}
