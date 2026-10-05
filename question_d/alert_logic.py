"""Streaming alert engine (Question D, Level 2). Written from scratch, no ML library.

It sees ONE reading at a time and never sees the ground-truth label.

Rules
  drop_out      HR reads 0, or the last FLAT_N readings are exactly identical (sensor stuck)
  spike         HR is more than JUMP bpm above the recent median while the person is still
  silent_drift  HR now is more than DRIFT_RISE bpm above HR ~5 min ago, with no movement
                during that whole time

Alert must fire within 5 s of a spike / drop-out start  -> rules above react immediately
Same event must not alert twice within 60 s             -> per-kind cooldown
"""
from collections import deque
import numpy as np

STILL = 0.3          # acc below this = person is still (walking is 0.8 - 2.5)


class AlertEngine:
    def __init__(self, jump=30.0, flat_n=3, drift_rise=8.0, drift_span=300,
                 cooldown=None):
        self.jump, self.flat_n = jump, flat_n
        self.drift_rise, self.drift_span = drift_rise, drift_span
        self.cooldown = cooldown or {"spike": 60, "drop_out": 60, "silent_drift": 300}
        self.recent = deque(maxlen=30)            # clean HR baseline (no spikes / drop-outs)
        self.raw = deque(maxlen=flat_n)           # last raw readings, for "stuck sensor"
        self.hist = deque(maxlen=drift_span)      # (hr, acc) of clean readings, for drift
        self.last_alert = {}                      # kind -> time of last alert

    def step(self, t, hr, acc):
        """Feed one reading. Returns (kind, message) if an alert fires, else None."""
        self.raw.append(hr)
        kind, msg = None, None

        if hr <= 0.0:
            kind, msg = "drop_out", f"Sensor lost: heart rate reads 0 at t={t}s"
        elif len(self.raw) == self.flat_n and len(set(self.raw)) == 1:
            kind, msg = "drop_out", f"Sensor stuck: HR frozen at {hr:.0f} bpm at t={t}s"
        elif (len(self.recent) >= 10 and acc < STILL
              and hr - float(np.median(self.recent)) > self.jump):
            base = float(np.median(self.recent))
            kind = "spike"
            msg = (f"Sudden heart-rate jump to {hr:.0f} bpm (+{hr - base:.0f} above "
                   f"your recent {base:.0f}) while still, t={t}s")

        if kind is None:                          # clean reading -> update baselines
            self.recent.append(hr)
            self.hist.append((hr, acc))
            if len(self.hist) == self.drift_span:
                h = np.array(self.hist)
                rise = h[-20:, 0].mean() - h[:20, 0].mean()
                if rise > self.drift_rise and h[:, 1].max() < STILL:
                    kind = "silent_drift"
                    msg = (f"Heart rate has crept up {rise:.0f} bpm over the last "
                           f"{self.drift_span // 60} min with no movement, t={t}s")
        elif kind == "spike":
            pass                                  # spike readings stay out of the baseline

        if kind and t - self.last_alert.get(kind, -10**9) >= self.cooldown[kind]:
            self.last_alert[kind] = t
            return kind, msg
        return None
