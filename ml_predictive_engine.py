import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

def train_optimized_model():
    conn = sqlite3.connect('smart_home.db')
    df = pd.read_sql_query("SELECT * FROM sensor_data", conn)
    conn.close()

    if len(df) < 500:
        print("Waiting for more sensor data...")
        return

    # Prioritize Manual Intent over AI Rule Labels
    # This is how we 'Sense Identity' through manual overrides
    df['final_label'] = df['manual_hvac_label'].fillna(df['ai_label'])
    
    X = df[['motion', 'temp', 'lux', 'hum', 'watts']]
    y = df['final_label'].fillna(0) 

    # We use the winner from our Notebook Analysis: Random Forest
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    joblib.dump(model, 'optimized_energy_model.pkl')
    print(f"✅ Production Model Retrained on {len(df)} behavioral records.")