# smart_home_project


// Add this at the end of your loop() to send data every second
void loop() {
  // ... your existing motion and servo logic ...

  // NEW: The "Data Packet" for the Dashboard
  Serial.print("DATA:");
  Serial.print(digitalRead(pirPin)); // Motion (0 or 1)
  Serial.print(",");
  Serial.print(digitalRead(sensorPin)); // Extra Sensor (0 or 1)
  Serial.println(); // The newline tells Python "End of Message"

  delay(500); // Don't flood the serial port
}