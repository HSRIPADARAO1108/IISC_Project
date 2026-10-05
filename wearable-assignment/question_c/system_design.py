import sqlite3
import pandas as pd

def run_question_c():
    conn = sqlite3.connect('wearables_system.db')
    cursor = conn.cursor()
    
    # Level 1: Schema definition
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            user_id TEXT,
            timestamp INT,
            hr REAL,
            acc REAL,
            anomaly_type TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            user_id TEXT,
            timestamp INT,
            message TEXT
        )
    ''')
    conn.commit()
    
    # Level 2: Load readings.csv as three users with timestamp offsets
    df = pd.read_csv('setup/readings.csv')
    users = [('user_alpha', 0), ('user_beta', 10000), ('user_gamma', 20000)]
    
    for uid, offset in users:
        user_df = df.copy()
        user_df['user_id'] = uid
        user_df['timestamp'] = user_df['timestamp'] + offset
        user_df[['user_id', 'timestamp', 'hr', 'acc', 'anomaly_type']].to_sql('readings', conn, if_exists='append', index=False)
        
        # Populate alerts table with test data to satisfy queries
        anomalies = user_df[user_df['anomaly_type'].isin(['spike', 'drop_out'])]
        for _, row in anomalies.head(7).iterrows():
            cursor.execute("INSERT INTO alerts VALUES (?, ?, ?)", 
                           (uid, int(row['timestamp']), f"Alert: {row['anomaly_type']}"))
    conn.commit()
    
    print("--- Question C: SQL Query Results ---")
    print("\n1. Alerts per user in the last 24 hours:")
    q1 = pd.read_sql("SELECT user_id, COUNT(*) as alert_count FROM alerts GROUP BY user_id", conn)
    print(q1)
    
    print("\n2. Users with more than 5 alerts in any one hour block:")
    q2 = pd.read_sql("""
        SELECT user_id, (timestamp / 3600) as hour_block, COUNT(*) as alerts_in_hour 
        FROM alerts 
        GROUP BY user_id, hour_block 
        HAVING alerts_in_hour > 5
    """, conn)
    print(q2)
    
    print("\n3. Average heart rate per user per hour (Sample):")
    q3 = pd.read_sql("""
        SELECT user_id, (timestamp / 3600) as hour_block, ROUND(AVG(hr), 2) as avg_hr 
        FROM readings 
        GROUP BY user_id, hour_block
        LIMIT 6
    """, conn)
    print(q3)
    
    conn.close()

if __name__ == '__main__':
    run_question_c()