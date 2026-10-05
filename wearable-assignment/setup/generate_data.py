import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Personal Seed S based on USN 1DA25SCS18 -> 2518
S = 2518
np.random.seed(S)

def generate_wearable_data():
    total_seconds = 7200
    time_index = np.arange(total_seconds)
    
    resting_hr = 60 + (S % 20) # 78 bpm
    drift = np.sin(np.linspace(0, 3 * np.pi, total_seconds)) * 3
    breathing = np.sin(np.linspace(0, 150 * np.pi, total_seconds)) * 1.5
    noise = np.random.normal(0, 1.0, total_seconds)
    
    hr = resting_hr + drift + breathing + noise
    acc = np.random.uniform(0.05, 0.2, total_seconds)
    
    label = ['normal'] * total_seconds
    anomaly_type = ['none'] * total_seconds
    
    # 3 walking periods (5 to 10 minutes each)
    walking_intervals = [(1200, 1800), (3600, 4200), (5400, 6000)]
    for start, end in walking_intervals:
        acc[start:end] = np.random.uniform(0.8, 2.5, (end - start))
        hr[start:end] += np.random.uniform(20, 30)
        for i in range(start, end):
            label[i] = 'walking'
            anomaly_type[i] = 'walking'

    # 20 Labelled anomalies
    anomaly_specs = [
        ('spike', 500, 8), ('drop_out', 1000, 15), ('silent_drift', 2200, 300),
        ('spike', 2800, 5), ('drop_out', 3300, 20), ('silent_drift', 4500, 300),
        ('spike', 5000, 6), ('drop_out', 6200, 12), ('silent_drift', 6500, 250),
        ('spike', 7000, 4), ('spike', 350, 5), ('drop_out', 900, 10),
        ('silent_drift', 1900, 300), ('spike', 2500, 7), ('drop_out', 3100, 15),
        ('silent_drift', 4800, 300), ('spike', 5200, 5), ('drop_out', 5800, 25),
        ('silent_drift', 6800, 200), ('spike', 7150, 4)
    ]
    
    for anom_type, start_idx, duration in anomaly_specs:
        end_idx = min(start_idx + duration, total_seconds)
        if anom_type == 'spike':
            hr[start_idx:end_idx] += np.random.uniform(42, 55)
            acc[start_idx:end_idx] = np.random.uniform(0.0, 0.1, end_idx - start_idx)
        elif anom_type == 'drop_out':
            hr[start_idx:end_idx] = 0.0
            acc[start_idx:end_idx] = 0.0
        elif anom_type == 'silent_drift':
            hr[start_idx:end_idx] += np.linspace(0, 16, end_idx - start_idx)
            acc[start_idx:end_idx] = np.random.uniform(0.0, 0.1, end_idx - start_idx)
            
        for i in range(start_idx, end_idx):
            label[i] = 'anomaly'
            anomaly_type[i] = anom_type

    df = pd.DataFrame({
        'timestamp': time_index, 'hr': np.round(hr, 2),
        'acc': np.round(acc, 4), 'label': label, 'anomaly_type': anomaly_type
    })
    
    os.makedirs('setup', exist_ok=True)
    df.to_csv('setup/readings.csv', index=False)
    
    # Plot full signal
    plt.figure(figsize=(14, 5))
    plt.plot(df['timestamp'], df['hr'], label='Heart Rate (bpm)', color='blue', alpha=0.6)
    anomalous = df[df['label'] == 'anomaly']
    plt.scatter(anomalous['timestamp'], anomalous['hr'], color='red', s=10, label='Anomalies', zorder=5)
    plt.title(f'Wearable Sensor Stream - Seed S={S}')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Heart Rate (bpm)')
    plt.legend()
    plt.savefig('setup/readings_plot.png', dpi=300)
    plt.close()
    print("Dataset and plot generated successfully!")

if __name__ == '__main__':
    generate_wearable_data()