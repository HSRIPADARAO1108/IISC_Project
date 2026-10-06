# AI-Driven Anomaly Detection and Monitoring System

Wearable heart-rate monitoring: detect spikes, sensor drop-outs and slow silent drifts, without false alarms while the person walks.

**Name:** Sripada Rao H  **USN:** 1DA25SCS18  **Seed S = 2518**
S = 2518, taken from the digits of USN 1DA25SCS18 (25 and 18), since the USN does not end in four digits.
Resting heart rate = 60 + (2518 mod 20) = 78 bpm. Every random step uses S.

All four questions (A, B, C, D) are answered at Levels 1, 2 and 3.
Decision log and AI usage declaration: `PERSONAL_INTELLIGENCE.md`.

## How to run

```bash
pip install -r requirements.txt
bash run_all.sh                     # generates data and runs A, B, C, D
```

Run the parts one by one:

```bash
python setup/generate_data.py       # readings.csv + readings_plot.png (7,200 rows)
python question_a/detect.py
python question_b/explain.py
python question_c/system_design.py
python question_c/capacity.py
python question_d/producer.py --speed 200   # fast replay (1 = real time)
python question_d/measure_delay.py
```

Live dashboard:

```bash
python -m streamlit run question_d/dashboard.py
```

Open it in the browser (in Codespaces: Ports tab, globe next to port 8501). In the sidebar set "Start at second" to 150, speed 5 to 10, then press "Start live replay".

## The data

`setup/generate_data.py` creates a two-hour recording at one reading per second: heart rate with slow drift, a breathing wave and noise, three walking periods (heart rate +20 to 30 bpm, normal), and 20 labelled anomalies: 8 spikes, 6 drop-outs (zero or frozen) and 6 silent drifts (+15 bpm over 5 minutes). The plot is in `setup/readings_plot.png`.

## What each question contains

| Folder | Level 1 | Level 2 | Level 3 |
|---|---|---|---|
| `question_a` | Isolation Forest, precision/recall/F1 per type, walking false alarms | NumPy-only rolling z-score, own precision/recall/F1 (asserted equal to scikit-learn) | `PREDICTION.md`, window experiment, missed-anomaly plots |
| `question_b` | Window-feature Isolation Forest with SHAP | Own one-feature-at-a-time perturbation method | Rank comparison on 5 alerts, one disagreement, 3 plain-language messages |
| `question_c` | `architecture.png`, `schema.sql` | `queries.sql` run on 3 users, output in `outputs/query_outputs.txt` | `capacity.md`: rows per day, writes per second, storage per month, what breaks at 100,000 users |
| `question_d` | Streamlit dashboard reading SQLite, anomalies marked | `producer.py` (one row per second) and own `alert_logic.py` | `measure_delay.py` and `outputs/delay_table.csv` |

## Key results (seed 2518)

**Question A**
- Isolation Forest (contamination 0.02): spike recall 1.00, drop-out recall 0.73, silent-drift recall 0.00, 0 false alarms during walking.
- Z-score (window 30, threshold 2.5, movement gate on): spike recall 0.82, precision 0.34, 0 walking false alarms. Without the gate: 79 walking false alarms.
- Silent drift is nearly invisible to both: it rises 0.05 bpm per second, so in a 30 s window the mean moves about 0.75 bpm while the noise is about 1.3 bpm. Doubling the window barely changes recall.

**Question B**
- 30 s windows with features such as mean, slope, minimum, maximum and movement. SHAP and my own perturbation method agree on spike and drop-out windows and disagree most on a drift window, because average and minimum heart rate are strongly correlated.
- This detector still alerts on 9 of 161 walking windows and does not flag the drift window. The streaming engine in Question D avoids both problems.

**Question C**
- 1,000 users: 86.4 million rows per day, 1,000 writes per second, about 207 GB per month. At 100,000 users the database write rate breaks first; the fix is a queue, batched inserts, time partitioning and downsampling.

**Question D**
- Alert engine rules: heart rate zero or frozen (drop-out); 30 bpm above the median of the last 30 clean readings while still (spike); 5 bpm above the value 5 minutes earlier while still (drift). 60 s cool-down per alert type.
- Average alert delay: spike 0 s, drop-out 0.5 s, silent drift 108.8 s. 0 false alarms in 20 alerts.

## Predictions

Level 3 predictions are in `question_a/PREDICTION.md`, `question_b/PREDICTION.md` and `question_d/PREDICTION.md` (committed in commit `9d244c8`, before the new experiments). Some earlier experiments were run before predictions were committed; this is stated in `PERSONAL_INTELLIGENCE.md`.

## Limitations

- Per-second Isolation Forest and z-score cannot detect the slow drift; only the streaming engine in Question D does.
- The data is simulated, not from a real device.
- The Question B detector is not movement-aware enough and alerts on some walking windows.

## Libraries and sources

numpy, pandas, scikit-learn (IsolationForest, metrics), shap (TreeExplainer), matplotlib, plotly, streamlit, sqlite3. Dashboard fonts: IBM Plex via Google Fonts. AI tools used (Claude, ChatGPT, Gemini) are declared in `PERSONAL_INTELLIGENCE.md`.