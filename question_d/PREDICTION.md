My first experiments were run before I committed predictions. This is my blind
prediction for a new experiment.

Experiment: lower the drift threshold from 8 bpm to 5 bpm.

Prediction:
- Average drift delay will fall from about 165 s to about 105 s.
- False alarms will not appear. Normal fluctuation over 5 minutes is only about 1 bpm, which is far below 5 bpm, and walking is blocked by the stillness check.
## Result
Experiment run after committing this prediction (commit 9d244c8): drift threshold 8 bpm -> 5 bpm.
- Average drift alert delay: 164.7 s -> 108.8 s (individual delays 80 to 125 s).
- Spike delay 0 s, drop-out delay 0.5 s on average.
- False alarms: 0 of 20 alerts.
