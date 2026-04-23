import sqlite3

# 1. Connect to the massive database
conn = sqlite3.connect('smart_home.db')
c = conn.cursor()

# 2. Fix the error records by setting them to a baseline (0)
print("Cleaning 1,010,820 records... please wait.")
c.execute("UPDATE sensor_data SET lux = 0 WHERE lux < 0")

conn.commit()
print(f"✅ Success! {c.rowcount} records cleaned.")
conn.close()