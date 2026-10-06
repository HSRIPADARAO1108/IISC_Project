My first experiments (window size, contamination, frozen-reading count) were run
before I committed predictions. This is my blind prediction for a new experiment.

Experiment: raise the z-score threshold from 3.5 to 2.5 (window 30, movement gate on).

Prediction:
- Spike recall will go up a little, because the later seconds of a spike still pass the lower threshold
- Walking false alarms will stay at 0, because the movement gate (acc < 0.3) blocks them whatever the threshold is.
- Precision will go down, because normal noise now crosses the threshold more often (more false alarms).
## Result
Experiment run after committing this prediction (commit 9d244c8): z-score threshold 3.5 -> 2.5, window 30 s, movement gate on.
- Spike recall: 0.490 -> 0.816. Spike precision: 0.585 -> 0.342.
- Walking false alarms: 0 with the gate (79 without the gate, 17 before the change).
- Drift recall stayed tiny (0.028) even though all 6 drift events show a flagged second, because the detector only hits isolated noisy seconds.
