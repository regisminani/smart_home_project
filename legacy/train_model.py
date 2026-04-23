import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

# 1. Load the data we generated in Task 3.1
df = pd.read_csv('energy_data.csv')

# 2. Select Features (X) and Target (y)
# We want to predict 'is_peak' using 'hour', 'temp', and 'occupancy'
X = df[['hour', 'temp', 'occupancy']]
y = df['is_peak']

# 3. Split data: 80% for training, 20% for testing the accuracy
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Initialize and Train the Random Forest
print("Training the AI model... please wait.")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 5. Check how smart the model is
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f"Model Training Complete! Accuracy: {accuracy * 100:.2f}%")

# 6. Save the model to a file (this is the 'brain' we will plug into Flask)
joblib.dump(model, 'energy_model.pkl')
print("Model saved as 'energy_model.pkl'")