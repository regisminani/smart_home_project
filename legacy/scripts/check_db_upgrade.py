import sqlite3
conn = sqlite3.connect('smart_home.db')
c = conn.cursor()
try:
    c.execute("ALTER TABLE sensor_data ADD COLUMN manual_hvac_label INTEGER")
    c.execute("ALTER TABLE sensor_data ADD COLUMN manual_light_label INTEGER")
    c.execute("ALTER TABLE sensor_data ADD COLUMN ai_label INTEGER")
    c.execute("ALTER TABLE sensor_data ADD COLUMN rule_label TEXT")
    print("✅ Database columns added.")
except sqlite3.OperationalError:
    print("ℹ️ Columns already exist.")
conn.close()