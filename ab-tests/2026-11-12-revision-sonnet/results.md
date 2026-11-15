# A/B test 21 results: the revised 0.13.0 against test 20's prompt-only and 0.12.0 builds, Sonnet 5.5 at medium effort

Arms: **A** = task only and **B** = task + test 20's dump read with 0.12.0's use mode (both arms' builds are test 20's own files); **D** = task + the same dump with its angles rewritten under the corrected brief, read with the revised 0.13.0 use mode. Builders and graders: Sonnet 5.5 at medium effort. Graders blind, 3 per block of 6, all grading fresh.

## Summary

| task | A | B (0.12.0) | D (0.13.0 revised) | D vs B | D vs A | B vs A |
|---|---|---|---|---|---|---|
| t2-pomodoro | 6.25 | 7.21 | **7.54** | 15–6–3 | 18–6–0 | 18–4–2 |
| t3-snowglobe | 7.08 | **7.25** | 6.08 | 3–20–1 | 7–17–0 | 9–11–4 |

## t2-pomodoro

Prompt: a simple pomodoro timer

| arm | simple | correctness | usability | craft | code | overall | per-run overall |
|---|---|---|---|---|---|---|---|
| A | 7.25 | 7.17 | 5.58 | 7.17 | 7.5 | **6.25** | 6.33, 6.67, 5.67, 6.33 |
| B | 5.67 | 8.33 | 8.0 | 7.42 | 5.75 | **7.21** | 8.0, 7.67, 7.67, 5.5 |
| D | 8.17 | 8.71 | 7.42 | 7.0 | 7.33 | **7.54** | 8.67, 4.0, 8.5, 9.0 |

D vs B head to head: 15 wins, 6 losses, 3 ties (win rate 0.69); permutation test on run means p = 0.8.
D vs A head to head: 18 wins, 6 losses, 0 ties (win rate 0.75); permutation test on run means p = 0.343.
B vs A head to head: 18 wins, 4 losses, 2 ties (win rate 0.79); permutation test on run means p = 0.143.

Grader agreement r = 0.92.

Builder cost per run: A 74401 tokens, 25.6 s; B 106757 tokens, 72.3 s; D 108500 tokens, 74.2 s.

## t3-snowglobe

Prompt: a snow globe

| arm | likeness | visuals | motion | presentation | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 7.83 | 6.92 | 6.58 | 7.33 | **7.08** | 8.67, 6.67, 8.33, 4.67 |
| B | 7.92 | 7.83 | 7.0 | 6.42 | **7.25** | 7.33, 5.67, 8.67, 7.33 |
| D | 7.42 | 6.33 | 6.08 | 6.25 | **6.08** | 5.33, 6.0, 6.33, 6.67 |

D vs B head to head: 3 wins, 20 losses, 1 ties (win rate 0.15); permutation test on run means p = 0.171.
D vs A head to head: 7 wins, 17 losses, 0 ties (win rate 0.29); permutation test on run means p = 0.343.
B vs A head to head: 9 wins, 11 losses, 4 ties (win rate 0.46); permutation test on run means p = 0.971.

Grader agreement r = 0.81.

Builder cost per run: A 85526 tokens, 83.7 s; B 127115 tokens, 208.5 s; D 120439 tokens, 165.4 s.

