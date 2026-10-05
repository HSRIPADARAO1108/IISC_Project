"""Question B: explain each alert.   python question_b/explain.py

Level 1  window-feature Isolation Forest + SHAP contributions per alert
Level 2  own one-feature-at-a-time perturbation (no SHAP / LIME)
Level 3  compare both rankings on five alerts, find a disagreement, write alert messages
"""
import os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap
from sklearn.ensemble import IsolationForest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from common import S, load

OUT = os.path.join(HERE, "outputs"); os.makedirs(OUT, exist_ok=True)
df = load()
hr, acc, atype = df.hr.to_numpy(), df.acc.to_numpy(), df.anomaly_type.to_numpy()

# ---------------- window features: 60 s windows, new window every 10 s ----------------
WIN, STEP = 30, 10
FEATS = ["hr_mean", "hr_std", "hr_min", "hr_max", "hr_slope", "acc_mean", "acc_std", "flat_run"]
PLAIN = {"hr_mean": "average heart rate", "hr_std": "heart-rate variability", "hr_min": "lowest heart rate",
         "hr_max": "highest heart rate", "hr_slope": "heart-rate trend", "acc_mean": "movement",
         "acc_std": "movement variation", "flat_run": "frozen readings"}
rows, meta = [], []
tt = np.arange(WIN)
for a in range(0, len(hr) - WIN + 1, STEP):
    h, c = hr[a:a + WIN], acc[a:a + WIN]
    same = np.r_[1, (np.diff(h) == 0).astype(int)]
    run, best = 0, 0
    for v in same[1:]:
        run = run + 1 if v else 0
        best = max(best, run)
    rows.append([h.mean(), h.std(), h.min(), h.max(), np.polyfit(tt, h, 1)[0], c.mean(), c.std(), best])
    w = atype[a:a + WIN]
    lab = "walking" if (w == "walking").mean() > 0.5 else "none"
    d = (w == "silent_drift").mean()
    if d >= 0.9:                                            # window sits fully inside a drift
        lab = "silent_drift"
    elif d > 0:                                             # half in / half out (includes the end-of-drift drop)
        lab = "mixed"
    for k in ("spike", "drop_out"):                         # short events: 3 seconds inside is enough
        if (w == k).sum() >= 3:
            lab = k
    meta.append((a, lab))
X = pd.DataFrame(rows, columns=FEATS)
meta = pd.DataFrame(meta, columns=["start", "label"])
print(f"S={S}  windows={len(X)}  label counts: {meta.label.value_counts().to_dict()}")

# ---------------- Level 1: detector + SHAP ----------------
clf = IsolationForest(n_estimators=200, contamination=0.04, random_state=S).fit(X)
score = lambda M: -clf.decision_function(M)                  # higher = more anomalous
sc = score(X)
alert = clf.predict(X) == -1
print(f"alerts raised: {alert.sum()}  | by true label: {meta.label[alert].value_counts().to_dict()}")
print("walking windows alerted:", int((alert & (meta.label == 'walking')).sum()),
      "of", int((meta.label == 'walking').sum()))

# pick 5 alerts: the strongest of each type, then fill with the next strongest alerts
chosen = []
for k in ("spike", "drop_out", "silent_drift"):
    idx = np.flatnonzero((meta.label == k).to_numpy())
    if len(idx):
        chosen.append(int(idx[np.argmax(sc[idx])]))
for i in np.argsort(-sc):
    if len(chosen) >= 5:
        break
    if i not in chosen and alert[i]:
        chosen.append(int(i))
print("explained windows (start second, label, flagged?):",
      [(int(meta.start[i]), meta.label[i], bool(alert[i])) for i in chosen])

normal_avg = X[(meta.label == "none").to_numpy()].mean()    # "normal period average" per feature
bg = X.sample(100, random_state=S)
sv = shap.TreeExplainer(clf, bg).shap_values(X.iloc[chosen])
# SHAP sign convention check: tree output moves with decision_function, so anomaly push = -SHAP
corr = np.corrcoef(sv.sum(1), clf.decision_function(X.iloc[chosen]))[0, 1] if len(chosen) > 2 else 1
shap_push = -sv if corr > 0 else sv
print(f"(SHAP sign check: corr(sum SHAP, decision_function)={corr:+.2f} -> "
      f"{'flipped so + means more anomalous' if corr > 0 else 'kept as is'})")

# ---------------- Level 2: own perturbation ----------------
def perturbation(i):
    """score drop when ONE feature is replaced by its normal-period average (+ = feature drove the alert)."""
    base, out = sc[i], []
    for f in FEATS:
        x = X.iloc[[i]].copy()
        x[f] = normal_avg[f]
        out.append(base - score(x)[0])
    return np.array(out)


pert = np.array([perturbation(i) for i in chosen])

# ---------------- Level 3: compare rankings ----------------
def ranks(v):                                                # rank 1 = biggest contributor
    return np.argsort(np.argsort(-v)) + 1


def spearman(a, b):
    ra, rb = ranks(a), ranks(b)
    return float(np.corrcoef(ra, rb)[0, 1])


print("\n--- SHAP vs own perturbation (top 3 features, + Spearman rank correlation) ---")
rho = []
for n, i in enumerate(chosen):
    ts, tp = np.argsort(-shap_push[n])[:3], np.argsort(-pert[n])[:3]
    rho.append(spearman(shap_push[n], pert[n]))
    print(f"t={int(meta.start[i]):4d}s [{meta.label[i]:12s}] score={sc[i]:.3f}  "
          f"SHAP top: {[FEATS[j] for j in ts]}  |  perturb top: {[FEATS[j] for j in tp]}  | rho={rho[-1]:+.2f}")
worst = int(np.argmin(rho))
i = chosen[worst]
print(f"\nBiggest disagreement: window t={int(meta.start[i])}s ({meta.label[i]}), rho={rho[worst]:+.2f}")
tbl = pd.DataFrame({"feature": FEATS, "value": X.iloc[i].values, "normal_avg": normal_avg.values,
                    "SHAP_push": shap_push[worst], "perturb_drop": pert[worst]}).round(3)
print(tbl.to_string(index=False))
corrm = X.corr().abs()
pairs = [(a, b, corrm.loc[a, b]) for a in FEATS for b in FEATS if a < b and corrm.loc[a, b] > 0.8]
print("highly correlated feature pairs (|r|>0.8) - perturbing one alone leaves its twin still extreme:")
for a, b, r in sorted(pairs, key=lambda x: -x[2])[:6]:
    print(f"   {a} ~ {b}: {r:.2f}")
tbl.to_csv(os.path.join(OUT, "disagreement_alert.csv"), index=False)

fig, ax = plt.subplots(1, len(chosen), figsize=(4 * len(chosen), 3.6), sharey=True)
for n, i in enumerate(chosen):
    y = np.arange(len(FEATS)); ax[n].barh(y - 0.2, shap_push[n], 0.4, label="SHAP")
    ax[n].barh(y + 0.2, pert[n], 0.4, label="own perturbation")
    ax[n].set_yticks(y); ax[n].set_yticklabels(FEATS); ax[n].invert_yaxis()
    ax[n].set_title(f"t={int(meta.start[i])}s {meta.label[i]}", fontsize=9)
ax[0].legend(fontsize=7); plt.tight_layout(); plt.savefig(os.path.join(OUT, "shap_vs_perturbation.png"), dpi=140)

# ---------------- plain-language messages built from real numbers ----------------
def message(n, i):
    k, v = meta.label[i], X.iloc[i]
    top = [PLAIN[FEATS[j]] for j in np.argsort(-pert[n])[:2]]
    if k == "spike":
        return (f"Your heart rate shot up to {v.hr_max:.0f} bpm (your normal is about {normal_avg.hr_max:.0f}) "
                f"while you were sitting still. Main signals: {top[0]} and {top[1]}.")
    if k == "drop_out":
        why = "read zero" if v.hr_min == 0 else f"froze at {v.hr_min:.0f} bpm"
        return (f"Your sensor stopped reporting: the heart rate {why} for part of this minute. "
                f"Check the strap fit. Main signals: {top[0]} and {top[1]}.")
    return (f"Your resting heart rate is creeping up by about {v.hr_slope * 60:.1f} bpm per minute without any "
            f"movement. Please rest and re-check. Main signals: {top[0]} and {top[1]}.")


print("\n--- Plain-language alert messages (one per type) ---")
lines = []
for k in ("spike", "drop_out", "silent_drift"):
    n = next(n for n, i in enumerate(chosen) if meta.label[i] == k)
    flagged = "" if alert[chosen[n]] else "  (note: the detector did NOT flag this window)"
    m = f"[{k}] t={int(meta.start[chosen[n]])}s: {message(n, chosen[n])}{flagged}"
    print(m); lines.append(m)
open(os.path.join(OUT, "alert_messages.txt"), "w").write("\n".join(lines))
