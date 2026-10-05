"""Shared helpers used by every question (seed, paths, data loading, metrics)."""
import os
import numpy as np
import pandas as pd

S = 2518                                   # personal seed = last four digits of USN
ROOT = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(ROOT, "setup", "readings.csv")
TYPES = ["spike", "drop_out", "silent_drift"]


def load():
    return pd.read_csv(CSV)


def segments(mask):
    """Return [(start, end_exclusive)] for each run of True in a boolean array."""
    idx = np.flatnonzero(mask)
    if len(idx) == 0:
        return []
    return [(int(g[0]), int(g[-1]) + 1) for g in np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)]


def my_prf(y, p):
    """Own precision / recall / F1 (no sklearn). y, p are 0/1 arrays."""
    y, p = np.asarray(y), np.asarray(p)
    tp = int(((y == 1) & (p == 1)).sum())
    fp = int(((y == 0) & (p == 1)).sum())
    fn = int(((y == 1) & (p == 0)).sum())
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
    return pr, rc, f1
