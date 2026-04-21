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

  // 2. Occupancy Logic (Red LED)
  if (motion == HIGH) {
    digitalWrite(RED_LED_PIN, HIGH);
  } else {
    digitalWrite(RED_LED_PIN, LOW);
  }

  // 3. HVAC Logic (Green LED)
  // Trigger if it's hot (over threshold) AND someone is in the room
  if (temp.temperature > TEMP_THRESHOLD && motion == HIGH) {
    digitalWrite(GREEN_LED_PIN, HIGH);
  } else {
    digitalWrite(GREEN_LED_PIN, LOW);
  }

  // 4. THE DATA PACKET (For the Python Bridge)
  // Format: DATA:Motion,Lux,Temp,Humidity,RawLDR
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

  delay(1000); // Send data every 1 second
}