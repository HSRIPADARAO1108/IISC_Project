# Personal intelligence note  (S = 2518)

> Rewrite every line in your own words and with your own numbers from YOUR runs. Keep it to one page.

## 1. Decision log (two per question: what I chose, one option I rejected, why, with evidence)

**A1 Isolation Forest contamination.** Chose ___; rejected ___. Evidence: the sweep printed in
`question_a/outputs/results.txt` (recall and walking false alarms at 0.02 / 0.04 / 0.06 / 0.10).
**A2 z-score movement gate.** Chose to ignore points with acc >= 0.3; rejected ungated z-score. Evidence: walking
false alarms with vs without the gate (same file).

**B1 Window length / features.** Chose 60 s windows with slope and flat-run features; rejected ___. Evidence: ___.
**B2 Which alerts to explain.** Chose ___; rejected ___. Evidence: `question_b/outputs/`.

**C1 Database choice / schema.** Chose SQLite with PRIMARY KEY (user_id, ts); rejected ___. Evidence: ___.
**C2 What breaks first at 100,000 users.** Chose ___ as the first bottleneck; rejected ___. Evidence: `question_c/capacity.md`.

**D1 Alert rule thresholds.** Chose jump = 30 bpm over the median of the last 30 clean readings; rejected a fixed
+40 bpm threshold. Evidence: noise and slow drift are about +/-6 bpm, so a 42 bpm spike can slip under +40.
**D2 Cool-down per kind.** Chose a 60 s cool-down per alert kind; rejected one global timer. Evidence: ___.

## 2. Predictions before results
Committed in `question_a/PREDICTION.md`, `question_b/PREDICTION.md`, `question_d/PREDICTION.md`
(the commit time is the proof). Summary of how each prediction compared with the result: ___.

## 3. AI usage declaration
Tools used: Claude (code scaffolding for generator, detectors, dashboard, README) ___ (add any others, and what
you used them for; be honest about what you wrote yourself).

One place the AI was wrong or weak, and how I found and fixed it (true examples from building this project;
choose one you actually checked yourself and describe it in your own words):
- The first Isolation Forest used raw HR plus rolling features; the per-type report showed 100+ false alarms
  during walking and zero drift recall. Fix: features gated on stillness (`hr_dev30_still`, `hr_delta240_still`).
- In question B the first window labels had no spike or drop-out windows at all (a 40% overlap rule is
  impossible for 5-20 s events inside a 60 s window). Found by printing the label counts; fixed with a 3-second rule.
- SHAP's sign convention for IsolationForest is opposite to "more anomalous"; checked by correlating the SHAP
  sum with `decision_function` before comparing rankings.

## 4. Live walkthrough: parts I must be able to explain and change without AI
`common.my_prf`, `rolling_z`, `AlertEngine.step`, `perturbation()`, `queries.sql`, `capacity.py`, `producer.py` loop.
