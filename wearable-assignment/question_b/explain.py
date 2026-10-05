import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

def run_question_b():
    df = pd.read_csv('setup/readings.csv')
    
    # Feature engineering for window features
    df['hr_mean'] = df['hr'].rolling(window=10, min_periods=1).mean()
    df['hr_std'] = df['hr'].rolling(window=10, min_periods=1).std().fillna(0)
    df['acc_mean'] = df['acc'].rolling(window=10, min_periods=1).mean()
    
    X = df[['hr', 'acc', 'hr_mean', 'hr_std', 'acc_mean']].values
    
    # Train Isolation Forest with seed S = 2518
    clf = IsolationForest(contamination=0.03, random_state=2518).fit(X)
    baseline_scores = clf.decision_function(X)
    
    # Level 2: Custom Feature Perturbation Method (No SHAP/LIME)
    normal_mask = df['label'] == 'normal'
    normal_means = {
        'hr': df.loc[normal_mask, 'hr'].mean(),
        'acc': df.loc[normal_mask, 'acc'].mean(),
        'hr_mean': df.loc[normal_mask, 'hr_mean'].mean(),
        'hr_std': df.loc[normal_mask, 'hr_std'].mean(),
        'acc_mean': df.loc[normal_mask, 'acc_mean'].mean()
    }
    
    # Analyze a known spike anomaly index (e.g., 500)
    anomaly_idx = 500
    print(f"--- Question B: Explaining Anomaly at Index {anomaly_idx} ---")
    print(f"Anomaly Type: {df.loc[anomaly_idx, 'anomaly_type']}, HR: {df.loc[anomaly_idx, 'hr']} bpm")
    
    feature_names = ['hr', 'acc', 'hr_mean', 'hr_std', 'acc_mean']
    drops = {}
    for idx, feat in enumerate(feature_names):
        X_perturbed = X.copy()
        X_perturbed[anomaly_idx, idx] = normal_means[feat]
        new_score = clf.decision_function(X_perturbed[anomaly_idx:anomaly_idx+1])[0]
        score_drop = new_score - baseline_scores[anomaly_idx] # Positive drop indicates how much feature drove anomaly
        drops[feat] = score_drop
        
    print("Feature Perturbation Impacts (Higher drop = major contributor to alert):")
    for feat, drop in sorted(drops.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {feat}: score shift of {drop:.4f}")

if __name__ == '__main__':
    run_question_b()