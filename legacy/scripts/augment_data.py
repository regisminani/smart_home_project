import sqlite3
import pandas as pd
import numpy as np

# 1. Connect to your database
conn = sqlite3.connect('smart_home.db')
df = pd.read_sql_query("SELECT * FROM sensor_data", conn)

current_count = len(df)
target_count = 1010820

if current_count < target_count:
    print(f"Current records: {current_count}. Augmenting to {target_count}...")
    
    # 2. Requirement 11.1: Random sampling with replacement
    additional_needed = target_count - current_count
    augmented_df = df.sample(n=additional_needed, replace=True)
    
    # 3. Add a tiny bit of "Noise" so they aren't exact copies
    # This keeps the "static properties" but mimics real sensor drift
    augmented_df['temp'] += np.random.normal(0, 0.1, size=len(augmented_df))
    augmented_df['watts'] += np.random.randint(-2, 3, size=len(augmented_df))
    
    # 4. Save back to the database
    augmented_df.to_sql('sensor_data', conn, if_exists='append', index=False)
    conn.commit()
    print(f"✅ Success! Total records now: {current_count + additional_needed}")
else:
    print(f"✅ You already have {current_count} records.")

conn.close()