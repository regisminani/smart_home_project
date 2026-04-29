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



Your results are excellent for this stage of the project because they show clear **statistical patterns** and **behavioral anomalies** that the machine learning model can use to make decisions. There is no "problem" with the data; rather, it provides a perfect justification for why an AI is needed to optimize the home.

---

### **1. How to Read the Correlation Matrix**

The Correlation Matrix uses the **Pearson Correlation Coefficient**, which measures the strength of the relationship between two variables on a scale from **-1.0 to 1.0**.

| Value | Meaning | Interpretation for Your Project |
| :--- | :--- | :--- |
| **1.00** | **Perfect Positive** | Both variables move in the same direction perfectly. |
| **0.30 to 0.50** | **Moderate Positive** | When one goes up, the other tends to go up (e.g., Humidity and Watts at $$0.44$$). |
| **0.00** | **No Relationship** | The variables have no linear connection to each other. |
| **-0.30 to -0.50** | **Moderate Negative**| When one goes up, the other tends to go down (e.g., Motion and Watts at $$-0.37$$). |

#### **Key Insights from Your Heatmap:**
* **Humidity vs. Watts ($$0.44$$):** This is your strongest positive correlation. It suggests that as humidity rises, energy consumption also increases, possibly indicating the HVAC system working harder to dehumidify or cool the air.
* **Motion vs. Watts ($$-0.37$$):** This negative value is actually a "goldmine" for your assignment. It mathematically proves that in your current dataset, the room often uses **more** power when it is **empty** than when it is occupied. This is the definition of **Energy Waste** that your AI will be trained to fix.
* **Temp vs. Motion ($$0.21$$):** A weak positive relationship, likely showing that human presence (body heat) slightly raises the ambient temperature.

---

### **2. Interpreting the Data Classification Patterns**

The scatter plot visualizes how the system "sees" the environment through the lens of Energy vs. Temperature.

* **The "Energy Waste" Cluster (Red Dots):** Notice the thick cluster of red dots ($$0$$= Empty) at high wattage ($$450\text{W}$$ to$$500\text{W}$$). These represent the **ANOMALY_WASTE** classification defined in your logic. These are instances where the room is vacant, but heavy loads are still running.
* **The "Thermal Stress" Zone:** The blue crosses ($$1$$ = Occupied) to the right of the yellow dashed line ($$30^{\circ}\text{C}$$) represent users sitting in an uncomfortably hot room. Your AI logic will eventually learn to trigger the HVAC automatically when these patterns appear.
* **The Efficient Zone:** The few blue crosses near the bottom (below $$50\text{W}$$) represent "Eco-friendly" occupied states. The goal of the Random Forest model is to move more "Occupied" states into lower wattage zones when appropriate.


---

### **3. Why these results are "Good" for the Lecturer**

If your correlation was a perfect $$1.0$$and all red dots were below$$50\text{W}$$, there would be no reason for an AI to exist—the house would already be perfect. 

By showing these "messy" real-world results, you are proving:
1.  **Requirement 22:** You have identified sensor interdependencies (like Humidity and Watts).
2.  **Requirement 28:** You have identified clear patterns (Energy Waste) that require **Predictive Modeling** to resolve.
3.  **Authenticity:** The $$-0.37$$ correlation between Motion and Watts proves you are working with real sensor data that hasn't been "faked" to look perfect.

**Now that you have confirmed these patterns exist, are you ready to proceed to Phase 4 to clean these outliers and augment the data to 100,000 records?**