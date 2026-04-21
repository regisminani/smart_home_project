import serial
import requests
import time

# --- CONFIGURATION ---
SERIAL_PORT = 'COM4'  # Matches your successful connection
BAUD_RATE = 9600
# FIX: Added '/api/' to match your app.py route
LOCAL_SERVER_URL = "http://127.0.0.1:5000/api/data-receiver"

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"✅ Connected to Arduino on {SERIAL_PORT}")
except Exception as e:
    print(f"❌ Error: {e}")
    exit()

while True:
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').strip()
        
        if line.startswith("DATA:"):
            try:
                # Arduino Format: DATA:Motion,Lux,Temp,Humidity,RawLDR
                parts = line.replace("DATA:", "").split(",")
                
                # Mapping data to match your app.py requirements
                payload = {
                    # app.py expects "Occupied" or "Empty" strings
                    "occupancy": "Occupied" if int(parts[0]) == 1 else "Empty",
                    # app.py uses "watts" for the energy meter
                    "watts": int(parts[4]), 
                    "temp": float(parts[2]),
                    "lux": float(parts[1]),
                    "humidity": float(parts[3])
                }

                # Push to Flask
                response = requests.post(LOCAL_SERVER_URL, json=payload)
                print(f"Data Synced -> {payload['occupancy']} | Temp: {parts[2]}°C | Status: {response.status_code}")

            except Exception as e:
                print(f"⚠️ Parsing Error: {e}")
    time.sleep(0.1)