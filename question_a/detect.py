"""Question A: detect the abnormal readings.  Run from anywhere:  python question_a/detect.py

Level 1  Isolation Forest (scikit-learn)
Level 2  rolling z-score in NumPy only + own precision/recall/F1, checked against scikit-learn
Level 3  window-size experiment (compare with question_a/PREDICTION.md) + missed-anomaly plots
"""
import os, sys, subprocess
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_recall_fscore_support

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from common import S, TYPES, load, segments, my_prf

OUT = os.path.join(HERE, "outputs"); os.makedirs(OUT, exist_ok=True)


class Tee:                                            # print to screen AND outputs/results.txt
    def __init__(self, f): self.f, self.o = f, sys.stdout
    def write(self, x): self.o.write(x); self.f.write(x)
    def flush(self): self.o.flush(); self.f.flush()
sys.stdout = Tee(open(os.path.join(OUT, "results.txt"), "w"))

df = load()
hr, acc, atype = df.hr.to_numpy(), df.acc.to_numpy(), df.anomaly_type.to_numpy()
EVENTS = [(t, a, b) for t in TYPES for a, b in segments(atype == t)]


def report(name, pred, quiet=False):
    """Per-type P/R/F1 (anomaly type vs normal+walking rows) + events caught + walking false alarms."""
    res = {}
    for t in TYPES:
        m = (atype == t) | (atype == "none") | (atype == "walking")
        y, p = (atype[m] == t).astype(int), pred[m]
        mine = my_prf(y, p)
        sk = precision_recall_fscore_support(y, p, average="binary", zero_division=0)[:3]
        assert np.allclose(mine, sk), (t, mine, sk)   # own function must equal scikit-learn
        caught = sum(bool(pred[a:b].any()) for a, b in segments(atype == t))
        res[t] = (*mine, caught, len(segments(atype == t)))
    w = atype == "walking"
    res["walking_fa"] = int(pred[w].sum())
    if not quiet:
        print(f"\n== {name} ==")
        for t in TYPES:
            P, R, F, c, n = res[t]
            print(f"  {t:13s} precision={P:.3f} recall={R:.3f} F1={F:.3f}   events caught {c}/{n}")
        print(f"  false alarms during walking: {res['walking_fa']} of {int(w.sum())} walking seconds")
    return res


# ===================== Level 1: Isolation Forest =====================
s = df.hr
def run_length_same(x, cap=10):
    """How many consecutive identical readings end at each row (catches a stuck sensor)."""
    out = np.ones(len(x))
    for i in range(1, len(x)):
        out[i] = min(out[i - 1] + 1, cap) if x[i] == x[i - 1] else 1
    return out


hr_mean10 = s.rolling(10, min_periods=1).mean()
feat = pd.DataFrame({
    "hr": s,
    "acc_mean30": df.acc.rolling(30, min_periods=1).mean(),             # movement context
    "hr_std10": s.rolling(10, min_periods=1).std().fillna(0),
    "hr_dev30_still": 0.0,                                               # jump vs recent, only when still
    "flat_run": run_length_same(hr),
    "hr_delta240_still": 0.0,                                            # slow rise, only if still all along
})
dev30 = (s - s.shift(1).rolling(30, min_periods=5).median()).fillna(0)
delta240 = (hr_mean10 - hr_mean10.shift(240)).fillna(0)
still30 = (df.acc.rolling(30, min_periods=1).max() < 0.3)
still240 = (df.acc.rolling(240, min_periods=1).max() < 0.3)
feat["hr_dev30_still"] = dev30.where(still30, 0.0)       # walking must not look like a spike
feat["hr_delta240_still"] = delta240.where(still240, 0.0)  # ...or like a drift
print("Seed S =", S)
print("\n--- Level 1: Isolation Forest, contamination sweep (used for the decision log) ---")
for c in [0.02, 0.04, 0.06, 0.10]:
    m = IsolationForest(n_estimators=200, contamination=c, random_state=S).fit(feat)
    r = report(f"IF c={c}", (m.predict(feat) == -1).astype(int), quiet=True)
    print(f"  contamination={c:.2f}: recall spike={r['spike'][1]:.2f} drop_out={r['drop_out'][1]:.2f} "
          f"drift={r['silent_drift'][1]:.2f} | walking false alarms={r['walking_fa']}")

CONTAM = 0.02
iso = IsolationForest(n_estimators=200, contamination=CONTAM, random_state=S).fit(feat)
iso_score = -iso.decision_function(feat)              # higher = more anomalous
pred_iso = (iso.predict(feat) == -1).astype(int)
res_iso = report(f"Isolation Forest (contamination={CONTAM})", pred_iso)

# ===================== Level 2: NumPy-only rolling z-score =====================
def rolling_z(x, w):
    """z-score of x[i] against the PAST w readings (current point excluded)."""
    z = np.zeros(len(x))
    for i in range(w, len(x)):
        win = x[i - w:i]
        sd = win.std()
        if sd > 1e-6:                                 # flat window -> undefined, treat as 0
            z[i] = (x[i] - win.mean()) / sd
    return z


def zdet(w, gate=True, thr=2.5):
    p = np.abs(rolling_z(hr, w)) > thr
    if gate:
        p &= acc < 0.3                                # moving => walking => normal
    return p.astype(int)


print("\n--- Level 2: NumPy z-score (own metric function verified against scikit-learn by assert) ---")
report("z-score w=30, NO movement gate", zdet(30, gate=False))
p30, p60 = zdet(30), zdet(60)
res30 = report("z-score w=30 with movement gate", p30)
res60 = report("z-score w=60 with movement gate", p60)

# ===================== Level 3: window size and missed anomalies =====================
print("\n--- Level 3: silent-drift recall when the window is doubled ---")
for w in [15, 30, 60, 120, 300]:
    r = report(f"w={w}", zdet(w), quiet=True)
    print(f"  w={w:3d}s  drift recall={r['silent_drift'][1]:.3f}  drift events caught={r['silent_drift'][3]}/6")
print("  -> compare with the prediction you committed in question_a/PREDICTION.md")
try:
    log = subprocess.run(["git", "log", "-1", "--format=%cI", "--", "question_a/PREDICTION.md"],
                         capture_output=True, text=True, cwd=os.path.dirname(HERE)).stdout.strip()
    print("  PREDICTION.md last committed:", log or "NOT COMMITTED YET (commit it before running!)")
except Exception:
    pass

z30 = rolling_z(hr, 30)


def least_detected(pred):
    frac = [pred[a:b].mean() for _, a, b in EVENTS]
    return EVENTS[int(np.argmin(frac))]


def plot_missed(pred, name, extra_line=None):
    kind, a, b = least_detected(pred)
    lo, hi = max(0, a - 150), min(len(hr), b + 150)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(range(lo, hi), hr[lo:hi], lw=0.8, label="heart rate")
    ax.axvspan(a, b, color="red", alpha=0.15, label=f"true {kind}")
    f = np.flatnonzero(pred[lo:hi]) + lo
    ax.scatter(f, hr[f], c="k", s=14, zorder=3, label="flagged by method")
    ax.set_title(f"{name}: least-detected anomaly ({kind}, t={a}-{b}s)"); ax.legend(); ax.set_xlabel("second")
    fig.savefig(os.path.join(OUT, f"missed_{name}.png"), dpi=150, bbox_inches="tight"); plt.close(fig)
    return kind, a, b


print("\n--- Level 3: one anomaly each method (mostly) missed ---")
k, a, b = plot_missed(pred_iso, "isolation_forest")
print(f"  Isolation Forest : {k} t={a}-{b}s, flagged {pred_iso[a:b].mean():.0%} of its seconds; "
      f"max anomaly score inside = {iso_score[a:b].max():.3f} vs threshold {-iso.offset_:.3f}")
k, a, b = plot_missed(p30, "zscore30")
print(f"  z-score (w=30)   : {k} t={a}-{b}s, flagged {p30[a:b].mean():.0%} of its seconds; "
      f"max |z| inside = {np.abs(z30[a:b]).max():.2f} vs threshold 3.5")
dr = [(a, b) for a, b in segments(atype == 'silent_drift')][0]
print(f"  drift reference  : slope {15/300:.3f} bpm/s -> within a 30 s window the mean moves only "
      f"{15/300*15:.2f} bpm, while the noise std is about {hr[100:130].std():.2f} bpm")
print("\nplots saved to question_a/outputs/")
