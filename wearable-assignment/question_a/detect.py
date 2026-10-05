import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_recall_fscore_support

def run_detection():
    df = pd.read_csv('setup/readings.csv')
    
    # Level 1: Isolation Forest (Seed S = 2518)
    df['hr_mean'] = df['hr'].rolling(window=10, min_periods=1).mean()
    df['hr_std'] = df['hr'].rolling(window=10, min_periods=1).std().fillna(0)
    X = df[['hr', 'acc', 'hr_mean', 'hr_std']]
    clf = IsolationForest(contamination=0.03, random_state=2518)
    df['iso_pred'] = np.where(clf.fit_predict(X) == -1, 1, 0)
    
    print("--- Isolation Forest Evaluation ---")
    for atype in ['spike', 'drop_out', 'silent_drift']:
        sub = df[(df['anomaly_type'] == atype) | (df['anomaly_type'] == 'none')]
        y_true = (sub['anomaly_type'] == atype).astype(int)
        y_pred = (sub['iso_pred'] == 1).astype(int)
        prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary', zero_division=0)
        print(f"[{atype}] -> Precision: {prec:.3f}, Recall: {rec:.3f}, F1: {f1:.3f}")

    # Level 2: NumPy Rolling Z-Score (No Pandas rolling, no sklearn)
    hr = df['hr'].values
    z_preds = np.zeros(len(hr))
    window = 30
    for i in range(len(hr)):
        start = max(0, i - window + 1)
        window_data = hr[start:i+1]
        mean, std = np.mean(window_data), np.std(window_data)
        if std > 0 and abs((hr[i] - mean) / std) > 3.5:
            z_preds[i] = 1
    df['np_pred'] = z_preds
    
    false_walking = df[(df['label'] == 'walking') & (df['np_pred'] == 1)].shape[0]
    print(f"\nNumPy Z-Score false alarms during walking: {false_walking}")

if __name__ == '__main__':
    run_detection()