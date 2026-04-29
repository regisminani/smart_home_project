from flask import Flask, render_template, jsonify, request
import joblib
import pandas as pd
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

# Load AI Model (Random Forest)
model = joblib.load('optimized_energy_model.pkl')

# Global State
latest_data = {
    "watts": 0, "temp": 0.0, "lux": 0.0, "humidity": 0.0,
    "occupancy": "Empty", "last_seen": 0,
    "last_motion_at": datetime.now().timestamp()
}
relay_states = {"1": False, "2": False}
manual_locks = {"1": 0, "2": 0} 
OVERRIDE_DURATION = 600 # 10 minutes in seconds

def init_db():
    conn = sqlite3.connect('smart_home.db')
    c = conn.cursor()
    # Updated Schema to include AI and Manual labels for the lecturer's requirements
    c.execute('''CREATE TABLE IF NOT EXISTS sensor_data
                 (timestamp DATETIME, motion INT, lux FLOAT, temp FLOAT, hum FLOAT, watts INT, 
                  manual_hvac_label INT, manual_light_label INT, ai_label INT, rule_label TEXT)''')
    conn.commit()
    conn.close()

init_db()

def classify_data_point(temp, watts, occupancy):
    """Surgical classification for visualization requirements."""
    if occupancy == "Empty":
        return ("ANOMALY_WASTE", "#f43f5e") if watts > 50 else ("ECO_STANDBY", "#10b981")
    return ("THERMAL_STRESS", "#f59e0b") if temp > 30 else ("ACTIVE_USER", "#3b82f6")

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/api/toggle-relay', methods=['POST'])
def toggle_relay():
    global relay_states, manual_locks
    data = request.get_json(force=True)
    relay_id = str(data.get("id")) 
    
    if relay_id in relay_states:
        relay_states[relay_id] = not relay_states[relay_id]
        new_state = 1 if relay_states[relay_id] else 0
        
        # ACTIVATE THE LOCK: Prevent AI from touching this relay for 10 mins
        manual_locks[relay_id] = datetime.now().timestamp()

        # LOG MANUAL OVERRIDE (For dynamic learning)
        conn = sqlite3.connect('smart_home.db')
        c = conn.cursor()
        column = "manual_light_label" if relay_id == "1" else "manual_hvac_label"
        c.execute(f"UPDATE sensor_data SET {column} = ? WHERE rowid = (SELECT MAX(rowid) FROM sensor_data)", (new_state,))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "state": relay_states[relay_id]})
    return jsonify({"status": "error"}), 400

@app.route('/api/data-receiver', methods=['POST'])
def receive_data():
    global latest_data, relay_states
    data = request.get_json(force=True, silent=True)
    if not data: return jsonify({"status": "error"}), 400
    
    try:
        occ_str = data.get("occupancy", "Empty")
        now_ts = datetime.now().timestamp()
        
        # 1. PERSISTENCE: Update motion timer only when motion is detected
        if occ_str == "Occupied":
            latest_data["last_motion_at"] = now_ts

        latest_data.update({
            "watts": int(data.get("watts", 0)), 
            "temp": float(data.get("temp", 0.0)),
            "lux": float(data.get("lux", 0.0)), 
            "humidity": float(data.get("humidity", 0.0)),
            "occupancy": occ_str, 
            "last_seen": now_ts
        })

        # 2. DYNAMIC SENSING LOGIC
        time_since_motion = now_ts - latest_data["last_motion_at"]
        IS_OCCUPIED = time_since_motion < 300  # 5-minute timeout window

        light_locked = (now_ts - manual_locks["1"]) < OVERRIDE_DURATION
        hvac_locked = (now_ts - manual_locks["2"]) < OVERRIDE_DURATION

        # DYNAMIC AI DECISION
        features = pd.DataFrame([[1 if IS_OCCUPIED else 0, latest_data["temp"], latest_data["lux"], 
                                  latest_data["humidity"], latest_data["watts"]]], 
                                columns=['motion', 'temp', 'lux', 'hum', 'watts'])
        ai_pred = int(model.predict(features)[0])

        # A. LIGHTING (Relay 1): Only update if NOT locked by user
        if not light_locked:
            if IS_OCCUPIED:
                if not relay_states["1"]:
                    relay_states["1"] = True if latest_data["lux"] < 250 else False
                else:
                    relay_states["1"] = True 
            else:
                relay_states["1"] = False

        # B. HVAC (Relay 2): Only update if NOT locked by user
        # AI pred 1 (Comfort) or 3 (Heat Stress) triggers HVAC
        if not hvac_locked:
            relay_states["2"] = True if (IS_OCCUPIED and ai_pred in [1, 3]) else False

        # 3. CLASSIFICATION for visualization
        rule_label, _ = classify_data_point(latest_data["temp"], latest_data["watts"], "Occupied" if IS_OCCUPIED else "Empty")

        # 4. SAVE TO DB (Matches updated init_db schema)
        conn = sqlite3.connect('smart_home.db')
        c = conn.cursor()
        c.execute("""INSERT INTO sensor_data (timestamp, motion, lux, temp, hum, watts, ai_label, rule_label) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                  (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1 if IS_OCCUPIED else 0, 
                   latest_data["lux"], latest_data["temp"], latest_data["humidity"], 
                   latest_data["watts"], ai_pred, rule_label))
        conn.commit()
        conn.close()

        return jsonify({"status": "success", "relay_1": relay_states["1"], "relay_2": relay_states["2"]}), 200
    except Exception as e:
        # This will now print the error to your console so you can see why it failed
        print(f"CRASH in receive_data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/sensor-data')
def get_sensor_data():
    global relay_states, latest_data
    now = datetime.now().timestamp()
    
    conn = sqlite3.connect('smart_home.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sensor_data")
    record_count = c.fetchone()[0]
    conn.close()

    time_since_motion = now - latest_data["last_motion_at"]
    logic_occupancy = "Occupied" if time_since_motion < 300 else "Empty"

    # Virtual Metering
    total_watts = latest_data["watts"] + (60 if relay_states["1"] else 0) + (150 if relay_states["2"] else 0)
    
    # AI Sourcing (Must use the SAME features as receive_data)
    features = pd.DataFrame([[1 if logic_occupancy == "Occupied" else 0, latest_data["temp"], 
                              latest_data["lux"], latest_data["humidity"], total_watts]], 
                            columns=['motion', 'temp', 'lux', 'hum', 'watts'])
    prediction = int(model.predict(features)[0])
    
    # Visual Class labels
    class_label, class_color = classify_data_point(latest_data["temp"], total_watts, logic_occupancy)

    return jsonify({
        "watts": total_watts, "temp": latest_data["temp"], "lux": latest_data["lux"],
        "humidity": latest_data["humidity"], "occupancy": logic_occupancy, 
        "total_records": record_count, "relay_1": relay_states["1"], "relay_2": relay_states["2"],
        "ai_suggestion": "ADAPTING TO BEHAVIOR" if prediction != 2 else "ANOMALY: High waste detected.",
        "class_label": class_label, "class_color": class_color,
        "online": (now - latest_data["last_seen"]) < 10
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)