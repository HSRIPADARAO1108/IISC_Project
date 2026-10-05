My first experiments (window size, contamination, frozen-reading count) were run
before I committed predictions. This is my blind prediction for a new experiment.

Experiment: raise the z-score threshold from 3.5 to 2.5 (window 30, movement gate on).

Prediction:
- Spike recall will go up a little, because the later seconds of a spike still pass the lower threshold
- Walking false alarms will stay at 0, because the movement gate (acc < 0.3) blocks them whatever the threshold is.
- Precision will go down, because normal noise now crosses the threshold more often (more false alarms).