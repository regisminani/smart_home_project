import sqlite3

def upgrade_db():
    conn = sqlite3.connect('smart_home.db')
    c = conn.cursor()
    try:
        # Add a column to track manual user actions (the "True" label)
        # 0: User wants OFF, 1: User wants ON, None: No manual action
        c.execute("ALTER TABLE sensor_data ADD COLUMN manual_hvac_label INTEGER")
        c.execute("ALTER TABLE sensor_data ADD COLUMN manual_light_label INTEGER")
        print("✅ Database upgraded with manual label columns.")
    except sqlite3.OperationalError:
        print("⚠️ Columns already exist.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    upgrade_db()