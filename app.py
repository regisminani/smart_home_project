from flask import Flask, render_template, jsonify, request
import joblib
import pandas as pd
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

# Load AI Model
model = joblib.load('energy_model.pkl')

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
    global latest_data
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"status": "error"}), 400
    try:
        occ_str = data.get("occupancy", "Empty")
        motion_int = 1 if occ_str == "Occupied" else 0
        watts = int(data.get("watts", 0))
        temp = float(data.get("temp", 0.0))
        lux = float(data.get("lux", 0.0))
        hum = float(data.get("humidity", 0.0))

        now_ts = datetime.now().timestamp()
        if occ_str == "Occupied":
            latest_data["last_motion_at"] = now_ts

        latest_data.update({
            "watts": watts, "temp": temp, "lux": lux, 
            "humidity": hum, "occupancy": occ_str, "last_seen": now_ts
        })

        conn = sqlite3.connect('smart_home.db')
        c = conn.cursor()
        c.execute("INSERT INTO sensor_data (timestamp, motion, lux, temp, hum, watts) VALUES (?, ?, ?, ?, ?, ?)", 
                  (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), motion_int, lux, temp, hum, watts))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/sensor-data')
def get_sensor_data():
    global relay_states, latest_data
    now = datetime.now().timestamp()

    # 1. Database Fetch (Requirement #4)
    conn = sqlite3.connect('smart_home.db')
    c = conn.cursor()
    # SQL Order: Use DESC for latest, ASC for oldest
    c.execute("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 1")
    row = c.fetchone()
    conn.close()

    if row:
        latest_data.update({
            "occupancy": "Occupied" if row[1] == 1 else "Empty",
            "lux": row[2], "temp": row[3], "humidity": row[4], "watts": row[5]
        })

    # 2. Autonomous Logic
    time_since_motion = now - latest_data["last_motion_at"]
    if latest_data["occupancy"] == "Occupied":
        relay_states["1"] = True
        latest_data["last_motion_at"] = now 
    elif latest_data["occupancy"] == "Empty" and time_since_motion > 15:
        relay_states["1"] = False

    # 3. AI Prediction
    occ_int = 1 if latest_data["occupancy"] == "Occupied" else 0
    features = pd.DataFrame([[datetime.now().hour, latest_data["temp"], occ_int]], 
                            columns=['hour', 'temp', 'occupancy'])
    prediction = model.predict(features)[0]

    # 4. Virtual Metering
    light_w = 60 if relay_states["1"] else 0
    fan_w = 150 if relay_states["2"] else 0
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
        "ai_suggestion": "PREDICTIVE ALERT: Peak usage expected." if prediction == 1 else "AI INSIGHT: System optimized.",
        "peak_status": "HIGH PEAK" if prediction == 1 else "NORMAL",
        "online": (now - latest_data["last_seen"]) < 10
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)