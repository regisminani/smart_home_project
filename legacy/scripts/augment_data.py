import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def augment_data(target_count=105000):
    conn = sqlite3.connect('smart_home.db')
    df = pd.read_sql_query("SELECT * FROM sensor_data", conn)
    
    if len(df) == 0:
        print("No data to augment. Run the sensors first!")
        return

    print(f"Original records: {len(df)}. Generating {target_count} synthetic records...")

    # Requirement 34: Sample existing values with replacement
    # This keeps the statistical distribution (Mean, Std Dev) of your real data
    synthetic_data = df.sample(n=target_count, replace=True).copy()

    # Create new timestamps for the synthetic data so they don't overlap
    base_time = datetime.now()
    synthetic_data['timestamp'] = [
        (base_time - timedelta(seconds=i)).strftime('%Y-%m-%d %H:%M:%S') 
        for i in range(target_count)
    ]

    # Add slight 'Noise' to make the data realistic (Requirement 39)
    synthetic_data['temp'] += np.random.normal(0, 0.1, target_count)
    synthetic_data['lux'] += np.random.normal(0, 5, target_count)
    
    # Save back to database
    synthetic_data.to_sql('sensor_data', conn, if_exists='append', index=False)
    conn.close()
    print("✅ Augmentation Complete. 100,000+ records available for training.")

if __name__ == "__main__":
    augment_data()