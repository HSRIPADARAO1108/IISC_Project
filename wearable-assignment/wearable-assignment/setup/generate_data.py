"""Creates the personal wearable recording: 7,200 rows (2 h @ 1 Hz) driven by seed S."""
import os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import S, ROOT, segments

rng = np.random.default_rng(S)
N = 7200
t = np.arange(N)

# ---- 1. Heart rate: resting level + slow drift + breathing wave + noise -------------
resting = 60 + (S % 20)                                   # 78 bpm for S = 2518
slow_drift = 3.0 * np.sin(2 * np.pi * t / 5400 + rng.uniform(0, 2 * np.pi))
breathing = 1.5 * np.sin(2 * np.pi * t / 4.5)             # ~4.5 s breathing-like wave
noise = rng.normal(0, 1.0, N)
hr = resting + slow_drift + breathing + noise

# ---- 2. Movement + three walking periods (5-10 min, HR +20..30 bpm) -----------------
acc = rng.uniform(0.05, 0.20, N)
label = np.array(["normal"] * N, dtype=object)
atype = np.array(["none"] * N, dtype=object)

walk_slots = [(900, 1500), (3000, 3600), (5400, 6000)]    # each slot allows 300-600 s
RAMP = 20
for lo, hi in walk_slots:
    dur = min(int(rng.integers(300, 601)), hi - lo)
    a, b = lo, lo + dur
    boost = rng.uniform(20, 30)
    env = np.ones(dur)
    env[:RAMP] = np.linspace(0, 1, RAMP)                  # HR rises smoothly
    env[-RAMP:] = np.linspace(1, 0, RAMP)                 # and recovers smoothly
    hr[a:b] += boost * env
    acc[a:b] = rng.uniform(0.8, 2.5, dur)
    label[a:b], atype[a:b] = "walking", "walking"

# ---- 3. Twenty labelled anomalies: 8 spike, 6 drop-out, 6 silent drift --------------
# (type, start_second, duration). Outside walking periods, never overlapping.
specs = [
    ("spike", 200, 6), ("drop_out", 400, 15), ("silent_drift", 500, 300),
    ("spike", 1560, 8), ("silent_drift", 1700, 300), ("drop_out", 2100, 20),
    ("spike", 2300, 5), ("silent_drift", 2450, 300),
    ("drop_out", 3700, 12), ("silent_drift", 3850, 300), ("spike", 4250, 7),
    ("drop_out", 4400, 18), ("spike", 4550, 6), ("silent_drift", 4700, 300),
    ("spike", 5150, 6), ("drop_out", 5250, 10),
    ("spike", 6100, 5), ("drop_out", 6250, 14), ("silent_drift", 6400, 300),
    ("spike", 6800, 6),
]
assert len(specs) == 20

flat_toggle = 0
for kind, s0, d in specs:
    e = s0 + d
    assert (label[s0:e] == "normal").all(), f"overlap at {s0}"
    if kind == "spike":                                   # > 40 bpm jump, no movement
        hr[s0:e] += rng.uniform(45, 60)
        acc[s0:e] = rng.uniform(0.0, 0.1, d)
    elif kind == "drop_out":                              # alternate: reads zero / reads flat
        hr[s0:e] = 0.0 if flat_toggle % 2 == 0 else hr[s0 - 1]
        flat_toggle += 1
        acc[s0:e] = 0.0
    else:                                                 # +15 bpm over 5 min, no movement
        hr[s0:e] += np.linspace(0, 15, d)
        acc[s0:e] = rng.uniform(0.0, 0.1, d)
    label[s0:e], atype[s0:e] = "anomaly", kind

df = pd.DataFrame({"timestamp": t, "hr": np.round(hr, 2), "acc": np.round(acc, 4),
                   "label": label, "anomaly_type": atype})
df.to_csv(os.path.join(ROOT, "setup", "readings.csv"), index=False)

# ---- Plot: full signal, walking shaded, anomalies marked -----------------------------
fig, ax = plt.subplots(2, 1, figsize=(15, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
ax[0].plot(df.timestamp, df.hr, lw=0.6, color="#1f77b4", label="heart rate (bpm)")
for k, c in {"spike": "red", "drop_out": "black", "silent_drift": "orange"}.items():
    m = (df.anomaly_type == k).to_numpy()
    ax[0].scatter(df.timestamp[m], df.hr[m], s=6, color=c, label=k, zorder=3)
for a, b in segments(atype == "walking"):
    ax[0].axvspan(a, b, color="green", alpha=0.12)
    ax[1].axvspan(a, b, color="green", alpha=0.12)
ax[0].set_ylabel("HR (bpm)"); ax[0].legend(loc="upper right", ncol=4, fontsize=8)
ax[0].set_title(f"Wearable recording, seed S={S} (green = walking, which is normal)")
ax[1].plot(df.timestamp, df.acc, lw=0.5, color="gray"); ax[1].set_ylabel("acc"); ax[1].set_xlabel("seconds")
plt.tight_layout(); plt.savefig(os.path.join(ROOT, "setup", "readings_plot.png"), dpi=150)
print(f"rows={len(df)}  resting={resting}  anomalies={len(specs)}  seed={S}")
print(df.anomaly_type.value_counts().to_string())
