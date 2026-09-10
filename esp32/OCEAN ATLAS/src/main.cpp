#include <Arduino.h>

#define TRIG_PIN 5
#define ECHO_PIN 18

float readDepth() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);

  digitalWrite(TRIG_PIN, LOW);

  unsigned long duration = pulseIn(ECHO_PIN, HIGH, 30000);

  if (duration == 0) {
    return -1.0;
  }

  return duration * 0.0343 / 2.0;
}

void setup() {
  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  digitalWrite(TRIG_PIN, LOW);

  Serial.println("=================================");
  Serial.println("OCEAN ATLAS - ESP32 DEPTH TEST");
  Serial.println("=================================");
}

void loop() {
  float distance = readDepth();

  if (distance < 0) {
    Serial.println("DEPTH:No echo");
  } else {
    Serial.print("DEPTH:");
    Serial.println(distance);
  }

  delay(500);
}