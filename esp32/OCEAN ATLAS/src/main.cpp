/**
 * Ocean Atlas – NodeMCU ESP32-S Multi-Sensor Firmware
 * =====================================================
 *
 * Hardware:
 *   HC-SR04 Ultrasonic  TRIG→GPIO5   ECHO→GPIO18
 *   Metal Detector/Buzzer output → GPIO34
 *   MPU6050 IMU          SDA→GPIO21   SCL→GPIO22   addr 0x68
 *   16×2 LCD             RS→13 EN→14 D4→27 D5→26 D6→25 D7→33
 *
 * IMPORTANT:
 *   GPIO34 is used as DIGITAL INPUT for the metal detector/buzzer state.
 *
 *   HIGH → Buzzer ON  → Metal TRUE
 *   LOW  → Buzzer OFF → Metal FALSE
 */

#include <Arduino.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <LiquidCrystal.h>

// ── Pin definitions ──────────────────────────────────────────────────────────
#define TRIG_PIN     5
#define ECHO_PIN     18
#define METAL_PIN    34      // Metal detector / buzzer output

// ── Device identity ──────────────────────────────────────────────────────────
#define DEVICE_ID    "ROV-01"
#define DEVICE_TOKEN "rov-esp32-key-001"

// ── Timing intervals (ms) ────────────────────────────────────────────────────
#define SENSOR_INTERVAL     100
#define TELEMETRY_INTERVAL  200
#define LCD_INTERVAL        1500

// ── MPU6050 I2C address ──────────────────────────────────────────────────────
#define MPU6050_ADDR 0x68

// ── LCD ──────────────────────────────────────────────────────────────────────
LiquidCrystal lcd(13, 14, 27, 26, 25, 33);

// ── Sensor data ──────────────────────────────────────────────────────────────
volatile float g_distanceCm = -1.0f;

// Metal detector status
volatile bool g_metalDetected = false;

// Raw digital state from metal detector
volatile bool g_buzzerState = false;

// MPU6050
volatile float g_accelX = 0.0f;
volatile float g_accelY = 0.0f;
volatile float g_accelZ = 1.0f;
volatile bool g_mpuOk = false;

// ── Timing state ─────────────────────────────────────────────────────────────
uint32_t lastSensorRead = 0;
uint32_t lastTelemetrySend = 0;
uint32_t lastLcdUpdate = 0;

bool lcdScreen2 = false;


// ════════════════════════════════════════════════════════════════════════════
// HC-SR04 – Ultrasonic
// ════════════════════════════════════════════════════════════════════════════

float readUltrasonic()
{
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);

  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000UL);

  if (duration == 0)
  {
    return -1.0f;
  }

  float cm = (float)duration * 0.034f / 2.0f;

  if (cm < 2.0f || cm > 400.0f)
  {
    return -1.0f;
  }

  return cm;
}


// ════════════════════════════════════════════════════════════════════════════
// METAL DETECTOR / BUZZER
// ════════════════════════════════════════════════════════════════════════════

bool readMetalDetector()
{
  /*
     GPIO34 is now treated as DIGITAL INPUT.

     HIGH → Buzzer ON
     LOW  → Buzzer OFF
  */

  int state = digitalRead(METAL_PIN);

  if (state == HIGH)
  {
    return true;
  }
  else
  {
    return false;
  }
}


// ════════════════════════════════════════════════════════════════════════════
// MPU6050 – raw register read
// ════════════════════════════════════════════════════════════════════════════

bool readMPU6050(float &ax, float &ay, float &az)
{
  Wire.beginTransmission(MPU6050_ADDR);

  Wire.write(0x3B);

  if (Wire.endTransmission(false) != 0)
  {
    return false;
  }

  Wire.requestFrom(
    (uint8_t)MPU6050_ADDR,
    (uint8_t)6
  );

  if (Wire.available() < 6)
  {
    return false;
  }

  int16_t AcX = (Wire.read() << 8) | Wire.read();
  int16_t AcY = (Wire.read() << 8) | Wire.read();
  int16_t AcZ = (Wire.read() << 8) | Wire.read();

  // ±2 g → 16384 LSB/g

  ax = AcX / 16384.0f;
  ay = AcY / 16384.0f;
  az = AcZ / 16384.0f;

  return true;
}


// ════════════════════════════════════════════════════════════════════════════
// MPU6050 INITIALIZATION
// ════════════════════════════════════════════════════════════════════════════

bool initMPU6050()
{
  Wire.begin(21, 22);

  Wire.beginTransmission(MPU6050_ADDR);

  Wire.write(0x6B);
  Wire.write(0x00);

  int err = Wire.endTransmission(true);

  if (err != 0)
  {
    Serial.printf(
      "[DEBUG] [MPU6050] Init failed (I2C error %d)\n",
      err
    );

    return false;
  }

  Serial.println("[DEBUG] [MPU6050] Initialised OK");

  return true;
}


// ════════════════════════════════════════════════════════════════════════════
// READ ALL SENSORS
// ════════════════════════════════════════════════════════════════════════════

void readAllSensors()
{
  // ── Ultrasonic ───────────────────────────────────────────────────────────

  g_distanceCm = readUltrasonic();


  // ── Metal detector / buzzer ──────────────────────────────────────────────

  g_buzzerState = readMetalDetector();

  // Direct relationship:
  //
  // Buzzer ON  → TRUE
  // Buzzer OFF → FALSE

  g_metalDetected = g_buzzerState;


  // ── MPU6050 ──────────────────────────────────────────────────────────────

  float ax;
  float ay;
  float az;

  bool ok = readMPU6050(ax, ay, az);

  g_mpuOk = ok;

  if (ok)
  {
    g_accelX = ax;
    g_accelY = ay;
    g_accelZ = az;
  }


  // ── Serial monitoring ────────────────────────────────────────────────────

  Serial.print("[METAL] GPIO34=");

  if (g_buzzerState)
  {
    Serial.print("HIGH");
  }
  else
  {
    Serial.print("LOW");
  }

  Serial.print(" | BUZZER=");

  if (g_buzzerState)
  {
    Serial.print("ON");
  }
  else
  {
    Serial.print("OFF");
  }

  Serial.print(" | METAL_DETECTED=");

  if (g_metalDetected)
  {
    Serial.println("TRUE");
  }
  else
  {
    Serial.println("FALSE");
  }
}


// ════════════════════════════════════════════════════════════════════════════
// LCD UPDATE
// ════════════════════════════════════════════════════════════════════════════

void updateLCD()
{
  lcd.clear();

  if (!lcdScreen2)
  {
    // ── Screen 1: Distance + Metal ────────────────────────────────────────

    lcd.setCursor(0, 0);

    if (g_distanceCm < 0)
    {
      lcd.print("Dist: No echo");
    }
    else
    {
      lcd.print("Dist: ");
      lcd.print(g_distanceCm, 1);
      lcd.print(" cm");
    }

    lcd.setCursor(0, 1);

    if (g_metalDetected)
    {
      lcd.print("METAL DETECTED!");
    }
    else
    {
      lcd.print("Metal: Clear");
    }
  }
  else
  {
    // ── Screen 2: MPU6050 ─────────────────────────────────────────────────

    lcd.setCursor(0, 0);

    if (!g_mpuOk)
    {
      lcd.print("MPU: ERROR");

      lcd.setCursor(0, 1);
      lcd.print("Check I2C wiring");
    }
    else
    {
      lcd.print("X:");
      lcd.print(g_accelX, 2);

      lcd.print(" Y:");
      lcd.print(g_accelY, 2);

      lcd.setCursor(0, 1);

      lcd.print("Z:");
      lcd.print(g_accelZ, 2);

      lcd.print("g");
    }
  }

  lcdScreen2 = !lcdScreen2;
}


// ════════════════════════════════════════════════════════════════════════════
// SEND TELEMETRY
// ════════════════════════════════════════════════════════════════════════════

void sendTelemetry()
{
  JsonDocument doc;

  doc["device_id"] = DEVICE_ID;
  doc["schema_version"] = 1;


  // ── Metal detector ───────────────────────────────────────────────────────

  doc["metal_detected"] = g_metalDetected;

  doc["buzzer_state"] = g_buzzerState;


  // ── Distance ─────────────────────────────────────────────────────────────

  if (g_distanceCm >= 0)
  {
    doc["distance_cm"] =
      round(g_distanceCm * 10.0f) / 10.0f;
  }
  else
  {
    doc["distance_cm"] = nullptr;
  }


  // ── MPU6050 ──────────────────────────────────────────────────────────────

  if (g_mpuOk)
  {
    doc["accel_x"] =
      round(g_accelX * 1000.0f) / 1000.0f;

    doc["accel_y"] =
      round(g_accelY * 1000.0f) / 1000.0f;

    doc["accel_z"] =
      round(g_accelZ * 1000.0f) / 1000.0f;
  }
  else
  {
    doc["accel_x"] = nullptr;
    doc["accel_y"] = nullptr;
    doc["accel_z"] = nullptr;
  }


  // ── GPS ──────────────────────────────────────────────────────────────────

  doc["latitude"] = nullptr;
  doc["longitude"] = nullptr;


  // ── JSON ─────────────────────────────────────────────────────────────────

  String payload;

  serializeJson(doc, payload);

  Serial.println(payload);
}


// ════════════════════════════════════════════════════════════════════════════
// SETUP
// ════════════════════════════════════════════════════════════════════════════

void setup()
{
  Serial.begin(115200);

  Serial.println();
  Serial.println("========================================");
  Serial.println("  OCEAN ATLAS – ESP32 ROV Firmware");
  Serial.println("========================================");


  // ── Ultrasonic GPIO ──────────────────────────────────────────────────────

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  digitalWrite(TRIG_PIN, LOW);


  // ── Metal detector / buzzer GPIO ─────────────────────────────────────────

  /*
     GPIO34 is input-only.

     The metal detector circuit must provide
     the HIGH/LOW signal to GPIO34.
  */

  pinMode(METAL_PIN, INPUT);


  // ── LCD ──────────────────────────────────────────────────────────────────

  lcd.begin(16, 2);

  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("Ocean Atlas");

  lcd.setCursor(0, 1);
  lcd.print("Starting...");


  // ── MPU6050 ──────────────────────────────────────────────────────────────

  g_mpuOk = initMPU6050();


  // ── Ready ────────────────────────────────────────────────────────────────

  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("ROV-01 Ready");

  lcd.setCursor(0, 1);
  lcd.print("USB Serial");


  Serial.println(
    "[DEBUG] [Setup] Complete - entering main loop"
  );

  Serial.println();
  Serial.println("Metal detector monitoring started");
  Serial.println("----------------------------------------");
}


// ════════════════════════════════════════════════════════════════════════════
// LOOP
// ════════════════════════════════════════════════════════════════════════════

void loop()
{
  uint32_t now = millis();


  // ── Read sensors every 100 ms ────────────────────────────────────────────

  if (now - lastSensorRead >= SENSOR_INTERVAL)
  {
    readAllSensors();

    lastSensorRead = now;
  }


  // ── LCD every 1.5 seconds ────────────────────────────────────────────────

  if (now - lastLcdUpdate >= LCD_INTERVAL)
  {
    updateLCD();

    lastLcdUpdate = now;
  }


  // ── Website telemetry every 200 ms ──────────────────────────────────────

  if (now - lastTelemetrySend >= TELEMETRY_INTERVAL)
  {
    sendTelemetry();

    lastTelemetrySend = now;
  }
}