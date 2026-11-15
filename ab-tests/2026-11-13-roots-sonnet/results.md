# A/B test 23 results: the one-page roots skill against 0.13.0 and the prompt alone, Sonnet 5.5 at medium effort

Arms: **A** = task only and **C** = task + a lite meta dump built by 0.13.0's Haiku swarm, read with 0.13.0's use mode (both arms' builds are test 22's own files); **R** = task + the one-page roots skill: the builder writes its own dump in one go, then builds. Builders and graders: Sonnet 5.5 at medium effort. Graders blind, 3 per block of 6, all grading fresh.

## Summary

| task | A | C (0.13.0, swarm dump) | R (roots) | R vs C | R vs A | C vs A |
|---|---|---|---|---|---|---|
| t1-lavalamp | 5.25 | **7.58** | 7.25 | 9–11–4 | 19–2–3 | 24–0–0 |
| t2-calculator | 7.17 | **8.5** | 7.75 | 5–16–3 | 16–6–2 | 20–0–4 |

## t1-lavalamp

Prompt: a lava lamp

| arm | likeness | visuals | motion | presentation | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 6.08 | 5.0 | 5.08 | 5.83 | **5.25** | 6.0, 5.0, 4.0, 6.0 |
| C | 8.08 | 8.0 | 6.83 | 7.92 | **7.58** | 7.67, 7.33, 8.33, 7.0 |
| R | 7.92 | 7.58 | 5.92 | 7.33 | **7.25** | 9.0, 5.67, 6.33, 8.0 |

R vs C head to head: 9 wins, 11 losses, 4 ties (win rate 0.46); permutation test on run means p = 0.771.
R vs A head to head: 19 wins, 2 losses, 3 ties (win rate 0.85); permutation test on run means p = 0.114.
C vs A head to head: 24 wins, 0 losses, 0 ties (win rate 1.0); permutation test on run means p = 0.029.

Grader agreement r = 0.93.

Builder cost per run: A 75246 tokens, 40.9 s; C 126001 tokens, 192.6 s; R 98444 tokens, 199.1 s. Dump: 196987 tokens reported for the main loop, 1484 s.

## t2-calculator

Prompt: a basic calculator

| arm | basic | correctness | usability | craft | code | overall | per-run overall |
|---|---|---|---|---|---|---|---|
| A | 8.92 | 7.83 | 7.0 | 6.75 | 8.33 | **7.17** | 7.67, 7.67, 6.83, 6.5 |
| C | 8.58 | 8.42 | 8.5 | 8.58 | 7.08 | **8.5** | 8.67, 8.33, 8.33, 8.67 |
| R | 7.25 | 8.42 | 8.0 | 8.5 | 7.08 | **7.75** | 6.33, 8.67, 8.17, 7.83 |

R vs C head to head: 5 wins, 16 losses, 3 ties (win rate 0.27); permutation test on run means p = 0.171.
R vs A head to head: 16 wins, 6 losses, 2 ties (win rate 0.71); permutation test on run means p = 0.4.
C vs A head to head: 20 wins, 0 losses, 4 ties (win rate 0.92); permutation test on run means p = 0.029.

Grader agreement r = 0.77.

Builder cost per run: A 73485 tokens, 24.5 s; C 108470 tokens, 84.3 s; R 83800 tokens, 100.8 s. Dump: 212391 tokens reported for the main loop, 1595 s.

