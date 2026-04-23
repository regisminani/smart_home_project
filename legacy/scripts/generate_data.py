import pandas as pd
import random

# Create a list for our data
data = []

for i in range(1000):  # 1,000 hours of history
    hour = i % 24
    temp = round(random.uniform(20, 30), 1)
    occupancy = 1 if (7 <= hour <= 8 or 17 <= hour <= 22) else random.choice([0, 1])
    
    # Logic: Base load + extra if occupied + extra during "Peak Hours"
    base_load = 50 
    occ_load = 200 if occupancy == 1 else 0
    peak_spike = 150 if (18 <= hour <= 21) else 0
    
    watts = base_load + occ_load + peak_spike + random.randint(-20, 20)
    
    # 1 if usage > 300W (Our definition of a 'Peak')
    is_peak = 1 if watts > 300 else 0
    
    data.append([hour, temp, occupancy, watts, is_peak])

# Save to CSV
df = pd.DataFrame(data, columns=['hour', 'temp', 'occupancy', 'watts', 'is_peak'])
df.to_csv('energy_data.csv', index=False)
print("Task 3.1: energy_data.csv generated successfully!")