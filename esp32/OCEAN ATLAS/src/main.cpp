/**
 * Ocean Atlas – NodeMCU ESP32-S Multi-Sensor Firmware
 * =====================================================
 * Hardware:
 *   HC-SR04 Ultrasonic  TRIG→GPIO5   ECHO→GPIO18 (via voltage divider!)
 *   Metal Detector       Signal→GPIO34 (ADC, 0-3.3 V)
 *   MPU6050 IMU          SDA→GPIO21   SCL→GPIO22   addr 0x68
 *   16×2 LCD             RS→13 EN→14 D4→27 D5→26 D6→25 D7→33
 *
 * Architecture:
 *   ESP32 → Wi-Fi → FastAPI /ws/ingest/ROV-01?token=rov-esp32-key-001
 *   Backend broadcasts to /ws/sensors → React SensorTelemetryPanel
 *   Backend forwards distance_cm → /ws/depth → LiveDepthChart
 *
 * IMPORTANT – WIRING NOTE:
 *   HC-SR04 ECHO outputs 5 V. Use a voltage divider before GPIO 18:
 *     ECHO → 1 kΩ → GPIO18
 *                ↓
 *              2 kΩ → GND
 *
 * ─────────────────────────────────────────────────────
 * CONFIGURE THESE BEFORE FLASHING:
 */
#define WIFI_SSID        "SANJAY LAPTOP"        // ← your network
#define WIFI_PASSWORD    "qwertyuiop"           // ← your password
#define SERVER_HOST      "192.168.137.16"      // PC Wi-Fi LAN IP
#define SERVER_PORT      8000
// ─────────────────────────────────────────────────────

#include <Arduino.h>
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <LiquidCrystal.h>

// ── Pin definitions ──────────────────────────────────────────────────────────
#define TRIG_PIN     5
#define ECHO_PIN     18
#define METAL_PIN    34   // ADC1 channel – GPIO 34 is input-only, safe for ADC

// ── Device identity ──────────────────────────────────────────────────────────
#define DEVICE_ID    "ROV-01"
#define DEVICE_TOKEN "rov-esp32-key-001"

// ── Timing intervals (ms) ────────────────────────────────────────────────────
#define SENSOR_INTERVAL    100    // read sensors every 100 ms
#define TELEMETRY_INTERVAL 1000   // send JSON every 1 second
#define LCD_INTERVAL       1500   // flip LCD screen every 1.5 s

// ── Metal detection threshold ────────────────────────────────────────────────
#define METAL_THRESHOLD_V  0.30f  // voltage above this → metal detected

// ── MPU6050 I2C address ──────────────────────────────────────────────────────
#define MPU6050_ADDR 0x68

// ── LCD (LiquidCrystal: RS, EN, D4, D5, D6, D7) ────────────────────────────
LiquidCrystal lcd(13, 14, 27, 26, 25, 33);

// ── WebSocket client ─────────────────────────────────────────────────────────
WebSocketsClient webSocket;

// ── Sensor data (updated every SENSOR_INTERVAL) ─────────────────────────────
volatile float g_distanceCm  = -1.0f;
volatile float g_metalVoltage = 0.0f;
volatile bool  g_metalDetected = false;
volatile float g_accelX = 0.0f;
volatile float g_accelY = 0.0f;
volatile float g_accelZ = 1.0f;   // default ~1g when flat
volatile bool  g_mpuOk  = false;

// ── Timing state ─────────────────────────────────────────────────────────────
uint32_t lastSensorRead  = 0;
uint32_t lastTelemetrySend = 0;
uint32_t lastLcdUpdate   = 0;
bool     lcdScreen2      = false;   // false=screen1 (distance+metal), true=screen2 (MPU)

// ── WebSocket reconnect state ────────────────────────────────────────────────
bool     wsConnected     = false;


// ════════════════════════════════════════════════════════════════════════════
// HC-SR04 – non-blocking read
// Returns distance in cm, or -1.0 if out of range / no echo
// ════════════════════════════════════════════════════════════════════════════
float readUltrasonic() {
  // Trigger pulse
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // pulseIn with 30 ms timeout (≈ 510 cm max range)
  long duration = pulseIn(ECHO_PIN, HIGH, 30000UL);

  if (duration == 0) {
    return -1.0f;   // no echo / out of range
  }

  float cm = (float)duration * 0.034f / 2.0f;

  // Sanity check – HC-SR04 reliable range: 2–400 cm
  if (cm < 2.0f || cm > 400.0f) {
    return -1.0f;
  }

  return cm;
}


// ════════════════════════════════════════════════════════════════════════════
// Metal detector – ADC read on GPIO 34
// Returns voltage 0–3.3 V
// ════════════════════════════════════════════════════════════════════════════
float readMetalVoltage() {
  int raw = analogRead(METAL_PIN);
  if (raw < 0 || raw > 4095) {
    return 0.0f;  // invalid ADC value
  }
  return (raw / 4095.0f) * 3.3f;
}


// ════════════════════════════════════════════════════════════════════════════
// MPU6050 – raw register read via Wire
// Returns true on success, fills ax/ay/az in g-force
// ════════════════════════════════════════════════════════════════════════════
bool readMPU6050(float &ax, float &ay, float &az) {
  // Burst-read 6 bytes starting at ACCEL_XOUT_H (0x3B)
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) {
    return false;
  }

  Wire.requestFrom((uint8_t)MPU6050_ADDR, (uint8_t)6);
  if (Wire.available() < 6) {
    return false;
  }

  int16_t AcX = (Wire.read() << 8) | Wire.read();
  int16_t AcY = (Wire.read() << 8) | Wire.read();
  int16_t AcZ = (Wire.read() << 8) | Wire.read();

  // ±2 g full-scale (default) → 16384 LSB/g
  ax = AcX / 16384.0f;
  ay = AcY / 16384.0f;
  az = AcZ / 16384.0f;
  return true;
}


// ════════════════════════════════════════════════════════════════════════════
// MPU6050 initialisation – wake the device
// ════════════════════════════════════════════════════════════════════════════
bool initMPU6050() {
  Wire.begin(21, 22);   // SDA, SCL

  // Wake MPU6050 (power management register 0x6B, write 0 to clear sleep bit)
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x6B);
  Wire.write(0x00);
  int err = Wire.endTransmission(true);

  if (err != 0) {
    Serial.printf("[MPU6050] Init failed (I2C error %d)\n", err);
    return false;
  }
  Serial.println("[MPU6050] Initialised OK");
  return true;
}


// ════════════════════════════════════════════════════════════════════════════
// Read all sensors and update globals
// ════════════════════════════════════════════════════════════════════════════
void readAllSensors() {
  // HC-SR04
  float dist = readUltrasonic();
  g_distanceCm = dist;

  // Metal detector
  float mv = readMetalVoltage();
  g_metalVoltage  = mv;
  g_metalDetected = (mv > METAL_THRESHOLD_V);

  // MPU6050
  float ax, ay, az;
  bool ok = readMPU6050(ax, ay, az);
  g_mpuOk = ok;
  if (ok) {
    g_accelX = ax;
    g_accelY = ay;
    g_accelZ = az;
  }
}


// ════════════════════════════════════════════════════════════════════════════
// LCD update – alternate between two screens
// ════════════════════════════════════════════════════════════════════════════
void updateLCD() {
  lcd.clear();

  if (!lcdScreen2) {
    // ── Screen 1: Distance + Metal status ────────────────────────────────
    lcd.setCursor(0, 0);
    if (g_distanceCm < 0) {
      lcd.print("Dist: No echo");
    } else {
      lcd.print("Dist: ");
      lcd.print(g_distanceCm, 1);
      lcd.print(" cm");
    }

    lcd.setCursor(0, 1);
    if (g_metalDetected) {
      lcd.print("METAL DETECTED!");
    } else {
      lcd.print("Metal: Clear");
    }
  } else {
    // ── Screen 2: MPU6050 X/Y/Z ──────────────────────────────────────────
    lcd.setCursor(0, 0);
    if (!g_mpuOk) {
      lcd.print("MPU: ERROR");
      lcd.setCursor(0, 1);
      lcd.print("Check I2C wiring");
    } else {
      // Row 0: X and Y
      lcd.print("X:");
      lcd.print(g_accelX, 2);
      lcd.print(" Y:");
      lcd.print(g_accelY, 2);
      // Row 1: Z
      lcd.setCursor(0, 1);
      lcd.print("Z:");
      lcd.print(g_accelZ, 2);
      lcd.print("g");
    }
  }

  lcdScreen2 = !lcdScreen2;   // flip for next update
}


// ════════════════════════════════════════════════════════════════════════════
// Build and send telemetry JSON via WebSocket
// ════════════════════════════════════════════════════════════════════════════
void sendTelemetry() {
  if (!wsConnected) {
    Serial.println("[WS] Not connected – skipping telemetry send");
    return;
  }

  JsonDocument doc;
  doc["device_id"]       = DEVICE_ID;
  doc["schema_version"]  = 1;
  // deviation_percentage: derive from metal voltage (0–100 scale) for legacy dashboard
  // Uses real metal voltage – NOT simulated. 0.30 V threshold maps to ~9 % deviation.
  doc["deviation_percentage"] = g_metalVoltage * 30.3f;

  // Real sensor values
  doc["metal_detected"] = g_metalDetected;
  doc["metal_voltage"]  = round(g_metalVoltage * 1000.0f) / 1000.0f;  // 3 decimal places

  if (g_distanceCm >= 0) {
    doc["distance_cm"] = round(g_distanceCm * 10.0f) / 10.0f;  // 1 decimal
  } else {
    doc["distance_cm"] = nullptr;   // out of range – send null
  }

  if (g_mpuOk) {
    doc["accel_x"] = round(g_accelX * 1000.0f) / 1000.0f;
    doc["accel_y"] = round(g_accelY * 1000.0f) / 1000.0f;
    doc["accel_z"] = round(g_accelZ * 1000.0f) / 1000.0f;
  } else {
    doc["accel_x"] = nullptr;
    doc["accel_y"] = nullptr;
    doc["accel_z"] = nullptr;
  }

  // GPS – not yet installed; send null for forward compatibility
  doc["latitude"]  = nullptr;
  doc["longitude"] = nullptr;

  String payload;
  serializeJson(doc, payload);
  webSocket.sendTXT(payload);

  // Mirror to Serial for debugging
  Serial.print("[TX] ");
  Serial.println(payload);
}


// ════════════════════════════════════════════════════════════════════════════
// WebSocket event handler
// ════════════════════════════════════════════════════════════════════════════
void onWebSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
  switch (type) {
    case WStype_CONNECTED:
      wsConnected = true;
      Serial.println("[WS] Connected to FastAPI");
      break;

    case WStype_DISCONNECTED:
      wsConnected = false;
      Serial.println("[WS] Disconnected – will auto-reconnect");
      break;

    case WStype_TEXT: {
      String msg = String((char*)payload);
      Serial.printf("[WS] Server: %s\n", msg.c_str());

      // Handle server commands (e.g. scan_mode)
      JsonDocument resp;
      if (!deserializeJson(resp, msg)) {
        const char* msgType = resp["type"];
        if (msgType && strcmp(msgType, "scan_mode") == 0) {
          Serial.printf("[WS] Fine-scan mode requested (confidence %.2f)\n",
                        resp["confidence"].as<float>());
        }
      }
      break;
    }

    case WStype_ERROR:
      Serial.println("[WS] Error");
      break;

    default:
      break;
  }
}


// ════════════════════════════════════════════════════════════════════════════
// Wi-Fi connection
// ════════════════════════════════════════════════════════════════════════════
void connectWiFi() {
  Serial.printf("[WiFi] Connecting to %s", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  uint32_t t0 = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (millis() - t0 > 30000UL) {
      Serial.println("\n[WiFi] Timeout – restarting ESP32");
      ESP.restart();
    }
  }

  Serial.printf("\n[WiFi] Connected. IP: %s\n", WiFi.localIP().toString().c_str());
}


// ════════════════════════════════════════════════════════════════════════════
// setup()
// ════════════════════════════════════════════════════════════════════════════
void setup() {
  Serial.begin(115200);
  Serial.println("\n========================================");
  Serial.println("  OCEAN ATLAS – ESP32 ROV Firmware");
  Serial.println("========================================");

  // ── GPIO init ────────────────────────────────────────────────────────────
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(TRIG_PIN, LOW);

  // GPIO 34 is input-only on ESP32 – analogRead only, no pinMode needed
  analogSetAttenuation(ADC_11db);   // 0–3.3 V full range for all ADC channels

  // ── LCD init ─────────────────────────────────────────────────────────────
  lcd.begin(16, 2);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Ocean Atlas");
  lcd.setCursor(0, 1);
  lcd.print("Starting...");

  // ── MPU6050 init ─────────────────────────────────────────────────────────
  g_mpuOk = initMPU6050();

  // ── Wi-Fi ────────────────────────────────────────────────────────────────
  connectWiFi();

  // ── WebSocket client setup ───────────────────────────────────────────────
  // URL: ws://<SERVER_HOST>:<SERVER_PORT>/ws/ingest/ROV-01?token=rov-esp32-key-001
  String wsPath = "/ws/ingest/" DEVICE_ID "?token=" DEVICE_TOKEN;
  webSocket.begin(SERVER_HOST, SERVER_PORT, wsPath);
  webSocket.onEvent(onWebSocketEvent);
  webSocket.setReconnectInterval(3000);  // auto-reconnect every 3 s

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("ROV-01 Ready");
  lcd.setCursor(0, 1);
  lcd.print(WiFi.localIP().toString());

  Serial.println("[Setup] Complete – entering main loop");
}


// ════════════════════════════════════════════════════════════════════════════
// loop() – millis()-based non-blocking scheduler
// ════════════════════════════════════════════════════════════════════════════
void loop() {
  uint32_t now = millis();

  // ── 1. Keep WebSocket connection alive ───────────────────────────────────
  webSocket.loop();

  // ── 2. Reconnect Wi-Fi if lost ───────────────────────────────────────────
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Lost – reconnecting...");
    connectWiFi();
  }

  // ── 3. Read all sensors (every SENSOR_INTERVAL ms) ──────────────────────
  if (now - lastSensorRead >= SENSOR_INTERVAL) {
    readAllSensors();
    lastSensorRead = now;
  }

  // ── 4. Update LCD (every LCD_INTERVAL ms, alternate screens) ────────────
  if (now - lastLcdUpdate >= LCD_INTERVAL) {
    updateLCD();
    lastLcdUpdate = now;
  }

  // ── 5. Send telemetry (every TELEMETRY_INTERVAL ms) ─────────────────────
  if (now - lastTelemetrySend >= TELEMETRY_INTERVAL) {
    sendTelemetry();
    lastTelemetrySend = now;
  }
}