# Personal intelligence note

Name: Sripada Rao H   USN: 1DA25SCS18   Seed S = 2518
(S = 2518 comes from the digits of my USN, 25 and 18, since the USN does not end in four digits.)

## 1. Decision log

**Question A**
1. *Isolation Forest contamination.* I chose 0.02 and rejected 0.04 and 0.10.
   Evidence (`question_a/outputs/results.txt`): walking false alarms were 0 at 0.02,
   60 at 0.04 and 393 at 0.10, while drop-out recall only rose from 0.73 to 0.89.
   I accepted the lower recall to avoid false alarms during walking.
2. *Movement gate in the z-score.* I chose to ignore seconds with acc >= 0.3 and
   rejected the ungated z-score. Evidence: at threshold 2.5 the ungated version had
   79 walking false alarms and the gated version had 0.

**Question B**
1. *Window length.* I chose 30 s windows and rejected 60 s. Evidence: with 60 s windows
   at contamination 0.04 the spike window at t=1560 was not flagged; with 30 s windows
   8 spike windows were flagged, because a 5 s spike fills more of a short window.
2. *Which alerts to explain.* I chose the highest-scoring window of each type plus the
   strongest others, and rejected using only flagged alerts. Evidence: the silent-drift
   window (t=4120) is never flagged by this detector, but I wanted all three types
   explained, so the message states that it was not flagged.

**Question C**
1. *Primary key.* I chose PRIMARY KEY (user_id, ts) and rejected an auto-number id.
   Reason: a repeated send of the same reading is rejected instead of duplicated.
2. *First bottleneck at 100,000 users.* I chose database write rate and rejected disk
   size. Evidence (`question_c/capacity.md`): 100,000 writes per second versus 1,000 at
   1,000 users; storage is about 20.7 TB per month and can simply be added.

**Question D**
1. *Spike rule.* I chose "30 bpm above the median of the last 30 clean readings" and
   rejected a fixed +40 bpm. Reason: normal drift and noise are about +/-6 bpm.
   Evidence: all 8 spikes were caught, with 0 false alarms in 20 alerts.
2. *Drift threshold.* I chose 5 bpm and rejected 8 bpm. Evidence: average drift delay fell
   from 164.7 s to 108.8 s, still with 0 false alarms.

## 2. Predictions before results

My first experiments (window sizes in A, contamination in B, frozen-reading count in D)
were run before I committed predictions. That was my mistake. My pre-registered
predictions are in `question_a/PREDICTION.md`, `question_b/PREDICTION.md` and
`question_d/PREDICTION.md`, committed at 20:43:36Z (commit 9d244c8) before the new runs
(z-score threshold 3.5 to 2.5, window 60 s to 30 s, drift threshold 8 to 5 bpm).
How they compared with the results (see the Result section in each file):
- A: lowering the threshold raised spike recall from 0.49 to 0.82 and cut precision from
  0.59 to 0.34; walking false alarms stayed at 0 thanks to the movement gate.
- B: the number of alerts stayed at 29, but spike windows became detectable.
- D: average drift delay fell from about 165 s to about 109 s with no false alarms.

## 3. AI usage declaration

I used three AI tools: Claude, ChatGPT and Gemini. Claude helped write most of the code
(data generator, detectors, SHAP comparison, SQL and capacity maths, alert engine,
Streamlit dashboard) and walked me through the git commands. I used ChatGPT to understand
the assignment requirements, review the project structure and code, spot issues in the
anomaly-detection and real-time alert logic, and understand how the components work. I used
Gemini to troubleshoot environment errors such as running the Streamlit command, to
structure the final multi-question codebase layout, and to check that the work meets the
assignment requirements across all four questions. I ran all the code myself, committed
it, and studied the results.

Where the AI was wrong or weak, and how it was found and fixed:
- The first Isolation Forest flagged more than 100 walking seconds and caught no drift.
  This showed up in the per-type report; it was fixed by making the features depend on stillness.
- The first window labels in Question B contained no spike or drop-out windows, because
  the rule needed 40% overlap and these events last only 5 to 20 s inside a 60 s window.
  Found by printing the label counts.
- The dashboard printed raw internal text under the delay table because of a one-line
  if/else expression; it was replaced with a normal if/else.
- Some pasted text ran as terminal commands and created junk files; I found them with
  `git ls-files` and removed them.

## 4. What I can explain and change without AI

`my_prf` and `rolling_z` (A), the perturbation loop (B), the three queries and capacity
steps (C), the three rules in `alert_logic.py` and the producer loop (D).