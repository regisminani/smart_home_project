from flask import Flask, render_template, jsonify, request
import joblib
import pandas as pd
from datetime import datetime
import sqlite3

app = Flask(__name__)

# Load AI Model
model = joblib.load('energy_model.pkl')

# Global State
latest_data = {
    "watts": 0, 
    "temp": 0.0, 
    "occupancy": "Empty", 
    "last_seen": 0,
    "last_motion_at": datetime.now().timestamp() # Track actual motion
}
relay_states = {"1": False, "2": False} # 1 = Light, 2 = Fan

def init_db():
    conn = sqlite3.connect('smart_home.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sensor_data
                 (timestamp DATETIME, motion INT, lux FLOAT, temp FLOAT, hum FLOAT, watts INT)''')
    conn.commit()
    conn.close()

init_db() # Run once on startup

@app.route('/')
def home():
    return render_template('dashboard.html')

# 1. Manual Control: Dashboard calls this
@app.route('/api/toggle-relay', methods=['POST'])
def toggle_relay():
    global relay_states, latest_data
    data = request.get_json(force=True)
    relay_id = str(data.get("id")) 
    
    if relay_id in relay_states:
        relay_states[relay_id] = not relay_states[relay_id]
        
        # --- FIX: MANUAL OVERRIDE ---
        # When you manually turn a light ON, we reset the motion timer 
        # to "now" so the Auto-Off doesn't kill it for 15 seconds.
        if relay_states[relay_id] == True:
            latest_data["last_motion_at"] = datetime.now().timestamp()
            
        print(f"Manual Toggle: Device {relay_id} is now {relay_states[relay_id]}")
        return jsonify({"status": "success", "state": relay_states[relay_id]})
    return jsonify({"status": "error"}), 400

@app.route('/api/set-relay', methods=['POST'])
def set_relay():
    global relay_states
    data = request.get_json(force=True)
    relay_id = str(data.get("id"))
    new_state = data.get("state") # True or False
    
    # This SETS the value instead of toggling it
    if relay_id in relay_states:
        relay_states[relay_id] = new_state
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

# 2. Command Fetch: ESP32 calls this
@app.route('/api/get-commands')
def get_commands():
    return jsonify(relay_states)

# 3. Data Receiver: ESP32 sends sensor data here
@app.route('/api/data-receiver', methods=['POST'])
def receive_data():
    global latest_data
    # Use force=True to handle JSON regardless of the Content-Type header
    data = request.get_json(force=True, silent=True)

    if not data:
        print("❌ Sync Failed: Payload was empty or malformed")
        return jsonify({"status": "error"}), 400

    try:
        # 1. Extraction & Normalization (Requirement #1 & #2)
        # Convert "Occupied" string to integer (1) for database efficiency
        occ_str = data.get("occupancy", "Empty")
        motion_int = 1 if occ_str == "Occupied" else 0
        
        # Meaningful unit extraction
        watts = int(data.get("watts", 0))
        temp = float(data.get("temp", 0.0))
        lux = float(data.get("lux", 0.0))
        hum = float(data.get("humidity", 0.0))

        # 2. Update Global State (Requirement #2 & #4)
        now_ts = datetime.now().timestamp()
        
        # Track actual motion for the 15s Auto-Off logic
        if occ_str == "Occupied":
            latest_data["last_motion_at"] = now_ts

        latest_data.update({
            "watts": watts,
            "temp": temp,
            "lux": lux,
            "humidity": hum,
            "occupancy": occ_str,
            "last_seen": now_ts
        })

        # 3. Local Database Mapping (Requirement #4)
        # Store all 4 sensors + timestamp in a single record
        db_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect('smart_home.db')
        c = conn.cursor()
        # Ensure column order matches your init_db(): timestamp, motion, lux, temp, hum, watts
        c.execute("INSERT INTO sensor_data (timestamp, motion, lux, temp, hum, watts) VALUES (?, ?, ?, ?, ?, ?)", 
                  (db_time, motion_int, lux, temp, hum, watts))
        conn.commit()
        conn.close()

        print(f"✅ DB & Sync Success: {occ_str} | {temp}°C | {watts}W")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"⚠️ Error during processing/DB write: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# 4. Dashboard Update: UI calls this every 1s
@app.route('/api/sensor-data')
def get_sensor_data():
    global relay_states, latest_data
    now = datetime.now().timestamp()

    # 1. Fetch the latest record from the Database
    conn = sqlite3.connect('smart_home.db')
    c = conn.cursor()
    # SQL Order Logic: DESC for latest, ASC for oldest
    c.execute("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 1")
    row = c.fetchone()
    conn.close()

    if row:
        # 2. UPDATE Global State so AI Logic uses DB values
        latest_data.update({
            "occupancy": "Occupied" if row[1] == 1 else "Empty",
            "lux": row[2],
            "temp": row[3],
            "humidity": row[4],
            "watts": row[5],
            "last_seen": now # Ensures the 'Online' dot stays green
        })

    # --- AUTO-ON/OFF LOGIC (Uses updated latest_data) ---
    time_since_motion = now - latest_data["last_motion_at"]
    if latest_data["occupancy"] == "Occupied":
        relay_states["1"] = True
        latest_data["last_motion_at"] = now 
    elif latest_data["occupancy"] == "Empty" and time_since_motion > 15:
        relay_states["1"] = False

    # --- AI PREDICTION ---
    current_hour = datetime.now().hour
    occ_int = 1 if latest_data["occupancy"] == "Occupied" else 0
    features = pd.DataFrame([[current_hour, latest_data["temp"], occ_int]], 
                            columns=['hour', 'temp', 'occupancy'])
    prediction = model.predict(features)[0]
    ai_msg = "PREDICTIVE ALERT: Peak usage expected." if prediction == 1 else "AI INSIGHT: System optimized."

    # --- VIRTUAL METERING ---
    light_w = 60 if relay_states["1"] else 0
    fan_w = 150 if relay_states["2"] else 0
    # FIX: Ensure total watts includes both raw DB sensor and virtual load
    total_dynamic_watts = latest_data["watts"] + light_w + fan_w

    return jsonify({
        "watts": total_dynamic_watts,
        "temp": latest_data["temp"],
        "lux": latest_data["lux"],
        "humidity": latest_data["humidity"],
        "occupancy": latest_data["occupancy"],
        "relay_1": relay_states["1"],
        "relay_2": relay_states["2"],
        "light_w": light_w,
        "fan_w": fan_w,
        "ai_suggestion": ai_msg,
        "peak_status": "HIGH PEAK" if prediction == 1 else "NORMAL",
        "online": (now - latest_data["last_seen"]) < 10
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)