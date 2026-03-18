from flask import Flask, render_template, jsonify, request
import joblib
import pandas as pd
from datetime import datetime

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
    # force=True is the key here; it ignores the header and tries to parse JSON anyway
    data = request.get_json(force=True, silent=True)
    
    if data:
        occ = data.get("occupancy", "Empty")
        if occ == "Occupied":
            latest_data["last_motion_at"] = datetime.now().timestamp()

        latest_data.update({
            "watts": int(data.get("watts", 0)),
            "temp": float(data.get("temp", 0)),
            "occupancy": occ,
            "last_seen": datetime.now().timestamp()
        })
        print(f"✅ Sync Success: {occ} | {latest_data['watts']}W")
        return jsonify({"status": "success"}), 200
    
    print("❌ Sync Failed: Payload was empty or malformed")
    return jsonify({"status": "error"}), 400

# 4. Dashboard Update: UI calls this every 1s
@app.route('/api/sensor-data')
def get_sensor_data():
    global relay_states
    now = datetime.now().timestamp()
    
    # Calculate time since the LAST "Occupied" signal
    time_since_motion = datetime.now().timestamp() - latest_data["last_motion_at"]
    
    # --- REQUIREMENT #1: AUTONOMOUS LOGIC (Server-Side) ---
    # 1. AUTO-ON: If motion is detected, force the light ON
# 1. AUTO-ON: If motion detected, turn it on
    if latest_data["occupancy"] == "Occupied":
        if not relay_states["1"]:
            print("AI System: Motion detected. Automatically enabling Light Grid.")
        relay_states["1"] = True
        # Keep updating the timer while we see motion
        latest_data["last_motion_at"] = now 

    # 2. AUTO-OFF: Only if room is empty AND 15s has passed
    elif latest_data["occupancy"] == "Empty" and time_since_motion > 15:
        if relay_states["1"]:
            print("AI System: Room empty for 15s. Automatically disabling Light Grid.")
        relay_states["1"] = False


    # AI Prediction
    current_hour = datetime.now().hour
    occ_int = 1 if latest_data["occupancy"] == "Occupied" else 0
    features = pd.DataFrame([[current_hour, latest_data["temp"], occ_int]], 
                            columns=['hour', 'temp', 'occupancy'])
    prediction = model.predict(features)[0]

    # Requirement Check: Predictive Insights (Actionable Suggestions)
    if prediction == 1:
        ai_msg = "PREDICTIVE ALERT: Peak usage expected soon. Suggestion: Shut down HVAC Fan."
        peak_status = "HIGH PEAK"
    else:
        ai_msg = "AI INSIGHT: System optimized. Current habits are sustainable."
        peak_status = "NORMAL"

    # Requirement Check: Individual Appliance Monitoring (Virtual Metering)
    # We "meter" them virtually based on their ON/OFF status
    light_w = 60 if relay_states["1"] else 0  # Assuming 60W bulb
    fan_w = 150 if relay_states["2"] else 0   # Assuming 150W fan
    total_dynamic_watts = latest_data["watts"] + light_w + fan_w

    return jsonify({
        "watts": total_dynamic_watts,
        "temp": latest_data["temp"],
        "occupancy": latest_data["occupancy"],
        "peak_status": peak_status,
        "relay_1": relay_states["1"],
        "relay_2": relay_states["2"],
        "light_w": light_w,
        "fan_w": fan_w,
        "ai_suggestion": ai_msg,
        "online": (datetime.now().timestamp() - latest_data["last_seen"]) < 10
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)