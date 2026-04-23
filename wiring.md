Using a **Green LED** as a "Mock HVAC" in the servo's place is a brilliant move for your demo. It provides immediate visual feedback that the AI's cooling logic is working, even without the heavy motor attached.

Here is the **complete, surgically precise mapping** of your entire system.

### 🧭 Breadboard Orientation & Setup
1.  **Hold the board vertically (Portrait):** Numbers **1–63** run top to bottom. Letters **a–e** are on the left; **f–j** are on the right.
2.  **Primary Power Rails:** * **Arduino 5V** $\rightarrow$ **Far Left Red (+) Rail**.
    * **Arduino GND** $\rightarrow$ **Far Left Blue (-) Rail**.
3.  **The I2C Junctions (SDA/SCL Bus):**
    * **Arduino A4 (SDA)** $\rightarrow$ **Row 10, Col a**.
    * **Arduino A5 (SCL)** $\rightarrow$ **Row 11, Col a**.

---

### 📍 Component Placement Map (Column E)
*All main components are placed with their pins in **Column e**, facing left.*

| Component | Pin Function | Row | Column | Note |
| :--- | :--- | :--- | :--- | :--- |
| **BH1750** | VCC | **5** | **e** | Digital Lux Sensor |
| | GND | **6** | **e** | |
| | SCL | **7** | **e** | |
| | SDA | **8** | **e** | |
| **AHT10** | VIN | **15** | **e** | Temp/Humidity |
| | GND | **16** | **e** | |
| | SCL | **17** | **e** | |
| | SDA | **18** | **e** | |
| **MH-LDR** | VCC | **25** | **e** | Analog Light Module |
| | GND | **26** | **e** | |
| | DO (Digital) | **27** | **e** | (Unused) |
| | **AO (Analog)** | **28** | **e** | |
| **PIR Sensor** | VCC | **35** | **e** | Motion Sensor |
| | **OUT** | **36** | **e** | |
| | GND | **37** | **e** | |
| **RED LED** (Occupancy) | **Long (+)** | **45** | **e** | Lights when occupied |
| | Short (-) | **46** | **e** | |
| **GREEN LED** (Mock HVAC) | **Long (+)** | **55** | **e** | Lights when "Fan" is ON |
| | Short (-) | **56** | **e** | |

---

### 🔌 Final Jumper & Resistor Mapping (Surgical Precision)

#### 1. Ground (-) Connections (All to Left Blue Rail)
* **Row 6, Col a** (BH1750 GND) $\rightarrow$ **Blue Rail**
* **Row 16, Col a** (AHT10 GND) $\rightarrow$ **Blue Rail**
* **Row 26, Col a** (MH-LDR GND) $\rightarrow$ **Blue Rail**
* **Row 37, Col a** (PIR GND) $\rightarrow$ **Blue Rail**
* **Row 46, Col a** (Red LED Short Leg) $\rightarrow$ **Blue Rail**
* **Row 56, Col a** (Green LED Short Leg) $\rightarrow$ **Blue Rail**

#### 2. Power (+) Connections (All to Left Red Rail)
* **Row 5, Col a** (BH1750 VCC) $\rightarrow$ **Red Rail**
* **Row 15, Col a** (AHT10 VIN) $\rightarrow$ **Red Rail**
* **Row 25, Col a** (MH-LDR VCC) $\rightarrow$ **Red Rail**
* **Row 35, Col a** (PIR VCC) $\rightarrow$ **Red Rail**

#### 3. I2C Data Bus (A4/A5)
* **Row 8, Col a** (BH1750 SDA) $\rightarrow$ **Row 10, Col b**
* **Row 18, Col a** (AHT10 SDA) $\rightarrow$ **Row 10, Col c**
* **Row 7, Col a** (BH1750 SCL) $\rightarrow$ **Row 11, Col b**
* **Row 17, Col a** (AHT10 SCL) $\rightarrow$ **Row 11, Col c**

#### 4. Signal Lines & Resistors (To Arduino Pins)
* **MH-LDR:** **Row 28, Col a** (AO) $\rightarrow$ **Arduino Analog A0**
* **PIR:** **Row 36, Col a** (OUT) $\rightarrow$ **Arduino Digital 7**
* **Red LED Resistor:**
    * Leg 1: **Row 45, Col a** (Connects to Red LED Long Leg)
    * Leg 2: **Row 45, Col f** (Crosses the gap) $\rightarrow$ Jumper from **Col j** to **Arduino Digital 6**
* **Green LED Resistor:**
    * Leg 1: **Row 55, Col a** (Connects to Green LED Long Leg)
    * Leg 2: **Row 55, Col f** (Crosses the gap) $\rightarrow$ Jumper from **Col j** to **Arduino Digital 9**

---

### 🟢 Why this is the perfect setup
1.  **Pin 6 (Red LED):** This is your **Occupancy Indicator**. If the PIR sees motion, the AI turns this on.
2.  **Pin 9 (Green LED):** This is your **Mock HVAC**. In your code, we will set a temperature threshold (e.g., 28°C). When it gets hot, the Green LED turns on. 
3.  **The Servo Switch:** When your MG995 arrives, you will simply unplug the Green LED and its resistor from **Rows 55 and 56** and plug the Servo's 3-pin connector directly into **Pin 9, 5V, and GND**.

### 🏁 Final Reality Check


* **Red LED:** Row 45 (+) to Pin 6.
* **Green LED:** Row 55 (+) to Pin 9.
* **Analog Sensor:** AO to Pin A0.
* **PIR:** Out to Pin 7.
* **I2C:** A4/A5 linked to Rows 10/11.

**Are the two LEDs sitting in the board now?** Once they are, give me the signal and I will give you the **complete final Arduino Code** that manages all 4 sensors and the "Mock HVAC" LED logic!