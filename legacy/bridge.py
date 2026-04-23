import serial
import requests
import time

# --- CONFIGURATION ---
SERIAL_PORT = 'COM3'  # Change this to your Arduino's COM port
BAUD_RATE = 9600
SERVER_URL = "http://127.0.0.1:5000/update"

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Connected to Arduino on {SERIAL_PORT}")
except:
    print("Could not connect to Arduino. Check the COM port!")
    exit()

while True:
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').strip()
        
        # Look for our "DATA:" prefix
        if line.startswith("DATA:"):
            try:
                # Split "DATA:1,0" into [1, 0]
                raw_data = line.replace("DATA:", "").split(",")
                motion = int(raw_data[0])
                sensor = int(raw_data[1])
                
                payload = {
                    "occupied": bool(motion),
                    "total_watts": 450 if motion else 20, # Simulated watts
                    "extra_sensor": bool(sensor)
                }

                # Push to Flask
                response = requests.post(SERVER_URL, json=payload)
                print(f"Sent: {payload} | Server Response: {response.status_code}")
                
            except Exception as e:
                print(f"Parse Error: {e}")