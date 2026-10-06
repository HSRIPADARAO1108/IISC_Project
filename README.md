# AI-Driven Anomaly Detection and Monitoring System (wearable heart-rate data)

**Seed S = 2518** (last four digits of USN). Resting HR = 60 + (2518 mod 20) = **78 bpm**. Every random step uses `S`.

## Run
```bash
pip install -r requirements.txt
python setup/generate_data.py          # readings.csv + readings_plot.png (7,200 rows, 20 anomalies, 3 walks)
python question_a/detect.py            # Isolation Forest, NumPy z-score, window experiment, missed plots
python question_b/explain.py           # SHAP vs own perturbation, 5 alerts, plain-language messages
python question_c/system_design.py     # architecture.png + 3 users in SQLite + 3 SQL queries
python question_c/capacity.py          # step-by-step capacity maths
python question_d/producer.py --speed 5                  # live replay (1 = real time)
python -m streamlit run question_d/dashboard.py          # live dashboard (or press "Start live replay")
python question_d/measure_delay.py                       # delay table (after a producer run)
```
`./run_all.sh` does the batch parts in one go.

## Contents
| Folder | Level 1 | Level 2 | Level 3 |
|---|---|---|---|
| `question_a` | Isolation Forest, per-type P/R/F1, walking false alarms | NumPy rolling z-score, own P/R/F1 asserted equal to scikit-learn | `PREDICTION.md`, window sweep, missed-anomaly plots |
| `question_b` | window-feature detector + SHAP | own perturbation method | rank comparison, one disagreement, 3 alert messages |
| `question_c` | `architecture.png`, `schema.sql` | `queries.sql` + `outputs/query_outputs.txt` | `capacity.md` |
| `question_d` | Streamlit dashboard reading SQLite | `producer.py` (1 row/s) + `alert_logic.py` | `measure_delay.py`, `outputs/delay_table.csv` |

Walking is never an anomaly: the z-score and the alert engine ignore HR jumps while `acc >= 0.3`.
`silent_drift` is caught in the live system by comparing HR with HR five minutes earlier while still; a
per-second z-score or Isolation Forest cannot see a 0.05 bpm/s climb (see question A, Level 3).

## Libraries and sources
numpy, pandas, scikit-learn (IsolationForest, metrics), shap (TreeExplainer), matplotlib, plotly, streamlit, sqlite3.
Dashboard fonts: IBM Plex via Google Fonts. AI assistance is declared in `PERSONAL_INTELLIGENCE.md`.

S = 2518, taken from the digits of USN 1DA25SCS18 (25 and 18), since the USN does not end in four digits.
