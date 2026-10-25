---
skill_name: Arduino Prototyping Guide
description: Build electronics projects with Arduino including circuits, sensors, actuators, serial communication, and WiFi connectivity
category: IoT & Hardware
version: 1.0.0
---

# Arduino Prototyping Guide

## Overview
Arduino enables rapid hardware prototyping. Master microcontrollers, sensors, and connectivity for IoT projects.

## Basic Setup

```cpp
void setup() {
  Serial.begin(9600);  // Initialize serial
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT);
}

void loop() {
  if (digitalRead(BUTTON_PIN) == HIGH) {
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(LED_PIN, LOW);
  }
  delay(100);
}
```

## Sensor Integration

```cpp
// Temperature sensor
#include <OneWire.h>
#include <DallasTemperature.h>

OneWire oneWire(2);
DallasTemperature sensors(&oneWire);

void setup() {
  sensors.begin();
}

void loop() {
  sensors.requestTemperatures();
  float tempC = sensors.getTempCByIndex(0);
  Serial.println(tempC);
  delay(1000);
}

// Accelerometer
#include <MPU6050.h>

MPU6050 mpu;

void setup() {
  mpu.initialize();
}

void loop() {
  int16_t ax, ay, az;
  mpu.getAcceleration(&ax, &ay, &az);
  Serial.print(ax); Serial.print(",");
  Serial.print(ay); Serial.print(",");
  Serial.println(az);
}
```

## Serial Communication

```cpp
// Send data to serial
void sendData(float value) {
  Serial.print("Value: ");
  Serial.println(value);
}

// Receive commands
void receiveCommand() {
  if (Serial.available() > 0) {
    char command = Serial.read();

    if (command == 'L') {
      digitalWrite(LED_PIN, HIGH);
    } else if (command == 'l') {
      digitalWrite(LED_PIN, LOW);
    }
  }
}

// JSON format
void sendJSON() {
  StaticJsonDocument<200> doc;
  doc["sensor"] = "temperature";
  doc["value"] = 25.5;
  doc["timestamp"] = millis();

  serializeJson(doc, Serial);
  Serial.println();
}
```

## WiFi Connectivity

```cpp
#include <WiFi.h>
#include <WebServer.h>

const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";

WebServer server(80);

void setup() {
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("Connected!");
  Serial.println(WiFi.localIP());

  server.on("/", handleRoot);
  server.on("/data", handleData);
  server.begin();
}

void loop() {
  server.handleClient();
}

void handleRoot() {
  server.send(200, "text/html", "<h1>Arduino Webserver</h1>");
}

void handleData() {
  float temp = readTemperature();
  server.send(200, "application/json", "{\"temp\":" + String(temp) + "}");
}

void readTemperature() {
  // Read from sensor
  return 25.5;
}
```

## Motor Control

```cpp
// DC Motor with PWM
const int motorPin = 9;
const int motorDirection = 8;

void setup() {
  pinMode(motorPin, OUTPUT);
  pinMode(motorDirection, OUTPUT);
}

void setMotor(int speed, bool direction) {
  // Speed: 0-255
  // Direction: true = forward, false = backward
  analogWrite(motorPin, abs(speed));
  digitalWrite(motorDirection, direction ? HIGH : LOW);
}

// Servo control
#include <Servo.h>

Servo servo;

void setup() {
  servo.attach(10);
}

void loop() {
  servo.write(90);  // Position 90 degrees
  delay(1000);
}

// Stepper motor
#include <Stepper.h>

const int stepsPerRevolution = 200;
Stepper stepper(stepsPerRevolution, 8, 9, 10, 11);

void setup() {
  stepper.setSpeed(60);  // RPM
}

void loop() {
  stepper.step(stepsPerRevolution);
  delay(500);
}
```

## Power Management

```cpp
// Sleep mode to save power
#include <avr/sleep.h>
#include <avr/power.h>

void sleepMode() {
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
  sleep_enable();
  sleep_cpu();
}

// Wake on interrupt
attachInterrupt(digitalPinToInterrupt(2), wakeUp, LOW);

void wakeUp() {
  sleep_disable();
}

// Battery monitoring
const int batteryPin = A0;

float readBattery() {
  int raw = analogRead(batteryPin);
  float voltage = (raw / 1023.0) * 5.0 * 2;  // 5V reference, 1:2 divider
  return voltage;
}
```

## Production Checklist

- [ ] Test all sensors independently
- [ ] Verify power supply
- [ ] Add proper current limiting
- [ ] Document pin assignments
- [ ] Implement error handling
- [ ] Add watchdog timer
- [ ] Test sleep modes
- [ ] Backup firmware
- [ ] Monitor memory usage
- [ ] Plan future expansion
