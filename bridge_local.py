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
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line.startswith("DATA:"):
            try:
                parts = line.replace("DATA:", "").split(",")
                payload = {
                    "occupancy": "Occupied" if int(parts[0]) == 1 else "Empty",
                    "watts": int(parts[4]), 
                    "temp": float(parts[2]),
                    "lux": float(parts[1]),
                    "humidity": float(parts[3])
                }

                # Push to Flask and get the Response
                response = requests.post(LOCAL_SERVER_URL, json=payload)
                res_data = response.json()

                # SURGICAL COMMAND: Send relay states back to Arduino
                if "relay_1" in res_data:
                    # Format: R:1,0 (Relay1=On, Relay2=Off)
                    r1 = 1 if res_data["relay_1"] else 0
                    r2 = 1 if res_data["relay_2"] else 0
                    cmd = f"R:{r1},{r2}\n"
                    ser.write(cmd.encode())
                    print(f"Sync -> {payload['occupancy']} | CMD Sent: {cmd.strip()}")

            except Exception as e:
                print(f"⚠️ Parsing Error: {e}")
    time.sleep(0.01) # Faster response for Context-Awareness