from flask import Flask, render_template, jsonify, request
import joblib
import pandas as pd
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

# Load AI Model
model = joblib.load('optimized_energy_model.pkl')

# Global State
latest_data = {
    "watts": 0, 
    "temp": 0.0, 
    "lux": 0.0,
    "humidity": 0.0,
    "occupancy": "Empty", 
    "last_seen": 0,
    "last_motion_at": datetime.now().timestamp()
}
relay_states = {"1": False, "2": False}

# --- NEW: Context-Aware User Preferences ---
USER_PREFS = {
    "Default": {"temp_threshold": 28.0, "light_timeout": 30, "hvac_timeout": 60, "lux_threshold": 200}, # Only turn on if below 200 lx
    "Nadine":  {"temp_threshold": 24.0, "light_timeout": 120, "hvac_timeout": 300, "lux_threshold": 400}, # Nadine likes it bright; triggers earlier
    "Regis":   {"temp_threshold": 26.5, "light_timeout": 60, "hvac_timeout": 120, "lux_threshold": 100}  # Regis is energy-efficient; triggers only when dark
}

# Track the active context
current_user = "Default"

def init_db():
    conn = sqlite3.connect('smart_home.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sensor_data
                 (timestamp DATETIME, motion INT, lux FLOAT, temp FLOAT, hum FLOAT, watts INT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/api/toggle-relay', methods=['POST'])
def toggle_relay():
    global relay_states, latest_data
    data = request.get_json(force=True)
    relay_id = str(data.get("id")) 
    if relay_id in relay_states:
        relay_states[relay_id] = not relay_states[relay_id]
        if relay_states[relay_id]:
            latest_data["last_motion_at"] = datetime.now().timestamp()
        return jsonify({"status": "success", "state": relay_states[relay_id]})
    return jsonify({"status": "error"}), 400

@app.route('/api/data-receiver', methods=['POST'])
def receive_data():
    global latest_data, relay_states, current_user
    data = request.get_json(force=True, silent=True)
    if not data: return jsonify({"status": "error"}), 400
    
    try:
        occ_str = data.get("occupancy", "Empty")
        now_ts = datetime.now().timestamp()
        current_lux = float(data.get("lux", 0.0))
        
        # 1. Update timestamp if motion detected
        if occ_str == "Occupied":
            latest_data["last_motion_at"] = now_ts

        # 2. Update sensor state
        latest_data.update({
            "watts": int(data.get("watts", 0)), 
            "temp": float(data.get("temp", 0.0)),
            "lux": current_lux, 
            "humidity": float(data.get("humidity", 0.0)), 
            "occupancy": occ_str, 
            "last_seen": now_ts
        })

        # 3. LUX-AWARE CONTEXT LOGIC
        prefs = USER_PREFS.get(current_user, USER_PREFS["Default"])
        time_since_motion = now_ts - latest_data["last_motion_at"]
        
        # A. LIGHTING LOGIC (Lux-Dependent)
        if time_since_motion < prefs["light_timeout"]:
            if not relay_states["1"]: # If turning ON for the first time
                relay_states["1"] = True if latest_data["lux"] < prefs["lux_threshold"] else False
            else:
                relay_states["1"] = True # Stay ON for persistence
        else:
            relay_states["1"] = False

        # B. HVAC LOGIC (Lux-Independent, Temp-Dependent)
        # We check the temperature threshold strictly
        if time_since_motion < prefs["hvac_timeout"]:
            if latest_data["temp"] > prefs["temp_threshold"]:
                relay_states["2"] = True
            else:
                # SURGICAL FIX: If temp drops below threshold, turn OFF immediately 
                # unless you want "Persistent Cooling" after the threshold is met.
                relay_states["2"] = False
        else:
            relay_states["2"] = False

        # HVAC Logic (Requires Light/Presence + Temperature)
        if relay_states["1"] and latest_data["temp"] > prefs["temp_threshold"]:
            relay_states["2"] = True
        elif time_since_motion > prefs["hvac_timeout"]:
            relay_states["2"] = False

        # 4. Save to DB
        conn = sqlite3.connect('smart_home.db')
        c = conn.cursor()
        c.execute("INSERT INTO sensor_data (timestamp, motion, lux, temp, hum, watts) VALUES (?, ?, ?, ?, ?, ?)", 
                  (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1 if occ_str == "Occupied" else 0, 
                   latest_data["lux"], latest_data["temp"], latest_data["humidity"], latest_data["watts"]))
        conn.commit()
        conn.close()

        return jsonify({"status": "success", "relay_1": relay_states["1"], "relay_2": relay_states["2"]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def classify_data_point(temp, watts, occupancy):
    """
    Surgical Requirement #9 & #10:
    Point-level classification algorithm.
    """
    if occupancy == "Empty":
        if watts > 50:
            return "ANOMALY_WASTE", "#f43f5e" # Red
        else:
            return "ECO_STANDBY", "#10b981"  # Green
    else: # Room is Occupied
        if temp > 30:
            return "THERMAL_STRESS", "#f59e0b" # Amber
        else:
            return "ACTIVE_USER", "#3b82f6"   # Blue
            
@app.route('/api/sensor-data')
def get_sensor_data():
    global relay_states, latest_data, current_user
    now = datetime.now().timestamp()

    # 1. Database Count (Requirement #4)
    conn = sqlite3.connect('smart_home.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sensor_data")
    record_count = c.fetchone()[0]
    conn.close()

    # 2. Match Sticky Occupancy Status for UI
    prefs = USER_PREFS.get(current_user, USER_PREFS["Default"])
    time_since_motion = now - latest_data["last_motion_at"]
    logic_occupancy = "Occupied" if time_since_motion < prefs["light_timeout"] else "Empty"

    # 3. Virtual Metering & AI Prediction
    light_w = 60 if relay_states["1"] else 0
    fan_w = 150 if relay_states["2"] else 0
    total_dynamic_watts = latest_data["watts"] + light_w + fan_w

    occ_int = 1 if logic_occupancy == "Occupied" else 0
    features = pd.DataFrame([[occ_int, latest_data["temp"], latest_data["lux"], latest_data["humidity"], total_dynamic_watts]], 
                            columns=['motion', 'temp', 'lux', 'hum', 'watts'])
    prediction = int(model.predict(features)[0])

    class_label, class_color = classify_data_point(latest_data["temp"], total_dynamic_watts, logic_occupancy)

    return jsonify({
        "watts": total_dynamic_watts,
        "temp": latest_data["temp"],
        "lux": latest_data["lux"],
        "humidity": latest_data["humidity"],
        "occupancy": logic_occupancy, 
        "user_context": current_user,
        "total_records": record_count,
        "relay_1": relay_states["1"],
        "relay_2": relay_states["2"],
        "ai_suggestion": f"CONTEXT: {current_user} profile active." if prediction != 2 else "ANOMALY: High waste detected.",
        "class_label": class_label,
        "class_color": class_color,
        "online": (now - latest_data["last_seen"]) < 10
    })

# Route to manually simulate switching users for the demo
@app.route('/api/set-user', methods=['POST'])
def set_user():
    global current_user
    data = request.get_json()
    user = data.get("user")
    if user in USER_PREFS:
        current_user = user
        return jsonify({"status": "success", "user": current_user})
    return jsonify({"status": "error"}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)