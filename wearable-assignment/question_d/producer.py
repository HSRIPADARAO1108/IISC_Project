import time
import sqlite3
import pandas as pd

def init_db():
    conn = sqlite3.connect('wearables.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS readings (timestamp INT, hr REAL, acc REAL, anomaly_type TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS alerts (timestamp INT, message TEXT)''')
    conn.commit()
    conn.close()

def run_producer():
    init_db()
    df = pd.read_csv('setup/readings.csv')
    conn = sqlite3.connect('wearables.db')
    
    last_alert_time = -60
    print("Starting real-time data stream simulation...")
    
    for _, row in df.iterrows():
        t = int(row['timestamp'])
        conn.execute("INSERT INTO readings VALUES (?, ?, ?, ?)", 
                     (t, row['hr'], row['acc'], row['anomaly_type']))
        
        # Alert Logic: Alert within 5s of spike/drop-out, 60s cooldown
        if row['anomaly_type'] in ['spike', 'drop_out'] and (t - last_alert_time >= 60):
            msg = f"ALERT: Detected {row['anomaly_type']} at t={t}s! HR: {row['hr']} bpm"
            conn.execute("INSERT INTO alerts VALUES (?, ?)", (t, msg))
            last_alert_time = t
            print(msg)
            
        conn.commit()
        time.sleep(0.002) # Acceleration factor for demo
    conn.close()
    print("Stream simulation finished.")

if __name__ == '__main__':
    run_producer()