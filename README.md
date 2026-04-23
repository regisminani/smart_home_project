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

# Bridge code

import serial
import requests
import time

# --- CONFIGURATION ---

SERIAL_PORT = 'COM3' # Check Arduino IDE for the correct COM port
BAUD_RATE = 9600

# IMPORTANT: This must be the ngrok URL from LAPTOP B

REMOTE_SERVER_URL = "http://dashboard-center.ngrok-free.app/update"

try:
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
print(f"Connected to Arduino. Sending data to Laptop B...")
except:
print("Error: Could not find Arduino. Is it plugged in?")
exit()

while True:
if ser.in_waiting > 0:
line = ser.readline().decode('utf-8').strip()

        if line.startswith("DATA:"):
            try:
                raw_data = line.replace("DATA:", "").split(",")
                payload = {
                    "occupied": bool(int(raw_data[0])),
                    "total_watts": 450 if int(raw_data[0]) else 25,
                    "extra_sensor": bool(int(raw_data[1]))
                }

                # Push the data across the internet to Laptop B
                headers = {"ngrok-skip-browser-warning": "69420"}
                response = requests.post(REMOTE_SERVER_URL, json=payload, headers=headers)

                print(f"Pushed to B: {payload} | Status: {response.status_code}")

            except Exception as e:
                print(f"Transmission Error: {e}")
    time.sleep(0.1)



# Starting venv 
source venv/Scripts/activate

# Collecting data

The Strategy:

Environment Variation: Physically blow on the AHT10 (Temp spike) and cover the LDR (Lux drop) while recording.

Turbo Polling: Change the Arduino delay(1000) to delay(100) and remove the time.sleep(0.1) in the Python bridge. This allows you to collect 10 records per second, hitting 100,000 records in about 2.7 hours instead of 27.

# SQL Logic to Change Order
You can modify this specific line in your Python query logic to toggle between viewing the latest data or the oldest historical data:

To display the LATEST (Default Dashboard):

SQL
SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 1;
To display the OLDEST (Historical Review):

SQL
SELECT * FROM sensor_data ORDER BY timestamp ASC LIMIT 1;

# Current record count check using terminal
import sqlite3
conn = sqlite3.connect('smart_home.db')
count = conn.execute("SELECT COUNT(*) FROM sensor_data").fetchone()[0]
print(f"Current Database Records: {count}")
conn.close()