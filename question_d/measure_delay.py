"""Question D, Level 3: delay from anomaly start to alert, for every detected anomaly.

Run the producer first (any speed). Two delays are reported:
  stream delay  = alert timestamp - anomaly start      (seconds of signal, speed independent)
  pipeline lag  = alert visible_at (committed to DB) - reading ingested_at (wall-clock, triggering row)
"""
import os, sqlite3, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from common import segments

DB = os.path.join(os.path.dirname(HERE), "wearables.db")
c = sqlite3.connect(DB)
r = pd.read_sql("SELECT * FROM readings ORDER BY timestamp", c)
a = pd.read_sql("SELECT * FROM alerts ORDER BY timestamp", c)
ing = r.set_index("timestamp").ingested_at
rows = []
for kind in ["spike", "drop_out", "silent_drift"]:
    for s, e in segments((r.truth == kind).to_numpy()):
        t_start, t_end = int(r.timestamp[s]), int(r.timestamp[e - 1])
        hit = a[(a.kind == kind) & (a.timestamp >= t_start) & (a.timestamp <= t_end)]
        if len(hit):
            h = hit.iloc[0]
            rows.append((kind, t_start, int(h.timestamp - t_start),
                         round((h.visible_at - ing[int(h.timestamp)]) * 1000, 2)))
        else:
            rows.append((kind, t_start, np.nan, np.nan))
d = pd.DataFrame(rows, columns=["kind", "start_s", "stream_delay_s", "pipeline_lag_ms"])
print(d.to_string(index=False))
fast = d[d.kind != "silent_drift"].dropna()
print(f"\nspike + drop-out : n={len(fast)}  avg={fast.stream_delay_s.mean():.2f}s  worst={fast.stream_delay_s.max():.0f}s")
for k, g in d.groupby("kind"):
    print(f"  {k:13s} caught {g.stream_delay_s.notna().sum()}/{len(g)}  avg delay {g.stream_delay_s.mean():.1f}s")
fa = a.merge(r[["timestamp", "truth"]], on="timestamp")
print(f"false alarms (alert on a row whose truth is 'none' or 'walking'): "
      f"{int(fa.truth.isin(['none', 'walking']).sum())} of {len(a)} alerts")
print(f"avg pipeline lag {d.pipeline_lag_ms.mean():.2f} ms (detector + DB commit; the dashboard adds its own refresh interval on top)")
os.makedirs(os.path.join(HERE, "outputs"), exist_ok=True)
d.to_csv(os.path.join(HERE, "outputs", "delay_table.csv"), index=False)
