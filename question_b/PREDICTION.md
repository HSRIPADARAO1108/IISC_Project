My first experiments were run before I committed predictions. This is my blind
prediction for a new experiment.

Experiment: change the window length from 60 s to 30 s.

Prediction:
- The number of alerted windows will stay about the same (around 29), because contamination fixes the share that gets flagged.- 
- For SHAP vs perturbation agreement, choose less (noisier features make the two methods rank differently) or more (more extreme features make the top feature obvious). Pick one and give your reason in one sentence. Both are defensible.
## Result
Experiment run after committing this prediction (commit 9d244c8): window 60 s -> 30 s.
- Alerts raised: 29 before and 29 after (contamination fixes the share of flagged windows).
- Spike windows became detectable: 8 of 24 spike windows flagged (none with 60 s windows).
- SHAP vs own perturbation rank agreement (Spearman rho) on the five alerts: about 0.8 for spike and drop-out windows, 0.60 for the drift window (0.52 before).
- 9 of 161 walking windows are still alerted by this detector, and the drift window is not flagged.
Was my prediction right? The alert count stayed at 29, as I predicted. My second bullet was left as template text when I committed, so I made no real prediction about SHAP agreement. The result is that agreement stayed about the same (0.8 for most windows, 0.60 for the drift window).