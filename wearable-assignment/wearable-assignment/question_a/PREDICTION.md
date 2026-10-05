# Question A, Level 3: prediction (COMMIT THIS BEFORE RUNNING detect.py)

Question: what happens to recall for silent drift if the rolling z-score window is doubled (30 s -> 60 s)?

My prediction (write it from the logic, in your own words):
- Direction: recall goes up / down / stays about the same because ...
- Rough number: ...
- Reasoning to use: drift rate is 15 bpm / 300 s = 0.05 bpm per second; compare how far the window mean moves
  with the noise standard deviation (about 1.3 bpm), and remember the z-score only sees the current point
  against the past window.

Committed at: (git log will show it)
