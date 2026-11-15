# A/B test 20 results: 0.13.0 against 0.12.0 and the prompt alone, three new tasks, Sonnet 5.5 at medium effort

Arms: **A** = task only; **B** = task + a lite meta dump, read with 0.12.0's use mode; **C** = task + the same dump, read with 0.13.0's use mode (deals rotate, the look plays the page). Dumps built fresh by 0.13.0's create mode (Haiku 5.5 swarm). Builders and graders: Sonnet 5.5 at medium effort, all arms fresh. Graders blind, 3 per block of 6.

## Summary

| task | A | B (0.12.0) | C (0.13.0) | C vs B | C vs A | B vs A |
|---|---|---|---|---|---|---|
| t1-fieldguide | 5.17 | 7.83 | **7.92** | 11–10–3 | 24–0–0 | 24–0–0 |
| t2-pomodoro | 7.08 | **7.79** | 6.71 | 5–17–2 | 7–12–5 | 16–6–2 |
| t3-snowglobe | 7.42 | **7.58** | 5.92 | 1–19–4 | 2–18–4 | 11–9–4 |

## t1-fieldguide

Prompt: a field guide entry for a dragon

| arm | imagination | fieldguide | specificity | voice | freshness | overall | per-run overall |
|---|---|---|---|---|---|---|---|
| A | 4.58 | 7.75 | 5.83 | 5.75 | 3.58 | **5.17** | 5.0, 6.0, 5.0, 4.67 |
| B | 7.5 | 8.5 | 8.17 | 7.58 | 7.42 | **7.83** | 8.0, 7.67, 8.33, 7.33 |
| C | 7.67 | 8.17 | 8.25 | 7.5 | 7.58 | **7.92** | 9.0, 7.0, 8.67, 7.0 |

C vs B head to head: 11 wins, 10 losses, 3 ties (win rate 0.52); permutation test on run means p = 0.943.
C vs A head to head: 24 wins, 0 losses, 0 ties (win rate 1.0); permutation test on run means p = 0.029.
B vs A head to head: 24 wins, 0 losses, 0 ties (win rate 1.0); permutation test on run means p = 0.029.

Grader agreement r = 0.95.

Builder cost per run: A 73470 tokens, 30.6 s; B 111844 tokens, 64.6 s; C 107167 tokens, 57.8 s. Dump: 192578 tokens reported for the main loop, 896 s.

## t2-pomodoro

Prompt: a simple pomodoro timer

| arm | simple | correctness | usability | craft | code | overall | per-run overall |
|---|---|---|---|---|---|---|---|
| A | 8.25 | 7.75 | 6.33 | 7.33 | 8.17 | **7.08** | 6.67, 7.0, 7.33, 7.33 |
| B | 6.5 | 8.5 | 8.33 | 7.58 | 6.42 | **7.79** | 8.83, 8.33, 8.67, 5.33 |
| C | 5.75 | 8.08 | 7.0 | 7.42 | 5.75 | **6.71** | 7.67, 5.83, 7.67, 5.67 |

C vs B head to head: 5 wins, 17 losses, 2 ties (win rate 0.25); permutation test on run means p = 0.229.
C vs A head to head: 7 wins, 12 losses, 5 ties (win rate 0.4); permutation test on run means p = 0.543.
B vs A head to head: 16 wins, 6 losses, 2 ties (win rate 0.71); permutation test on run means p = 0.543.

Grader agreement r = 0.78.

Builder cost per run: A 74401 tokens, 25.6 s; B 106757 tokens, 72.3 s; C 111821 tokens, 94.8 s. Dump: 219811 tokens reported for the main loop, 1273 s.

## t3-snowglobe

Prompt: a snow globe

| arm | likeness | visuals | motion | presentation | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 8.42 | 7.0 | 6.75 | 7.42 | **7.42** | 7.67, 7.33, 8.67, 6.0 |
| B | 8.33 | 7.75 | 7.08 | 6.58 | **7.58** | 8.67, 6.67, 8.33, 6.67 |
| C | 6.08 | 7.17 | 6.42 | 6.08 | **5.92** | 6.33, 5.67, 7.0, 4.67 |

C vs B head to head: 1 wins, 19 losses, 4 ties (win rate 0.12); permutation test on run means p = 0.086.
C vs A head to head: 2 wins, 18 losses, 4 ties (win rate 0.17); permutation test on run means p = 0.114.
B vs A head to head: 11 wins, 9 losses, 4 ties (win rate 0.54); permutation test on run means p = 0.886.

Grader agreement r = 0.84.

Builder cost per run: A 85526 tokens, 83.7 s; B 127115 tokens, 208.5 s; C 138100 tokens, 281.1 s. Dump: 206141 tokens reported for the main loop, 1471 s.

