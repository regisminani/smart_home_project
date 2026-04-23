#include <Wire.h>
#include <BH1750.h>
#include <Adafruit_AHTX0.h>

// --- Configuration ---
const int PIR_PIN = 7;
const int RED_LED_PIN = 6;    // Occupancy Indicator
const int GREEN_LED_PIN = 9;  // Mock HVAC (Servo substitute)
const int LDR_ANALOG_PIN = A0; // MH-LDR Module
const float TEMP_THRESHOLD = 28.0; // Temp to trigger "Fan" (Green LED)

// --- Sensor Objects ---
BH1750 lightMeter;
Adafruit_AHTX0 aht;

void setup() {
  Serial.begin(9600);
  Wire.begin(); // Initializes I2C for BH1750 and AHT10

  // Initialize Pins
  pinMode(PIR_PIN, INPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(GREEN_LED_PIN, OUTPUT);

  // Initialize Sensors
  if (!aht.begin()) {
    Serial.println("Could not find AHT10 sensor!");
  }
  
  if (!lightMeter.begin()) {
    Serial.println("Could not find BH1750 sensor!");
  }

  Serial.println("SYSTEM_READY");
}

void loop() {
  // 1. Read Sensors
  sensors_event_t humidity, temp;
  aht.getEvent(&humidity, &temp);
  float lux = lightMeter.readLightLevel();
  int rawLDR = analogRead(LDR_ANALOG_PIN);
  int motion = digitalRead(PIR_PIN);

  // 2. RECEIVE COMMANDS FROM PYTHON 
  // This replaces the old blinking logic
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    if (cmd.startsWith("R:")) {
      // Parse format "R:1,0"
      int r1 = cmd.substring(2,3).toInt();
      int r2 = cmd.substring(4,5).toInt();
      digitalWrite(RED_LED_PIN, r1 == 1 ? HIGH : LOW);
      digitalWrite(GREEN_LED_PIN, r2 == 1 ? HIGH : LOW);
    }
  }

  // 3. THE DATA PACKET (Arduino -> Python)
  Serial.print("DATA:");
  Serial.print(motion);
  Serial.print(",");
  Serial.print(lux);
  Serial.print(",");
  Serial.print(temp.temperature);
  Serial.print(",");
  Serial.print(humidity.relative_humidity);
  Serial.print(",");
  Serial.println(rawLDR);

  delay(500); // Faster updates for smoother context response
}