# A/B test 17 results: three tasks, Sonnet 5.5 at medium effort, metadump 0.8.0 (the best-scoring version)

Arms: **A** = task only; **B** = task + a lite meta dump (test 12's dumps, built by metadump 0.8.0, read with 0.8.0's use mode). Builders and graders: Sonnet 5.5 at medium effort. Graders blind, 3 per block of 4.

## Summary

| task | A overall | B overall | B vs A win rate | p |
|---|---|---|---|---|
| t1-button | **8.08** | 5.75 | 0.02 | 0.029 |
| t2-haiku | 5.25 | **7.5** | 0.88 | 0.086 |
| t3-toast | **7.33** | 6.62 | 0.35 | 0.286 |

## t1-button

Prompt: a button with custom bezier curve hover state animations that makes it feel dreamlike and ethereal, but practical for a website

| arm | dreamlike | practical | motion | craft | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 8.5 | 6.92 | 8.25 | 8.17 | **8.08** | 8.33, 8.33, 7.33, 8.33 |
| B | 4.25 | 8.83 | 6.17 | 7.0 | **5.75** | 5.0, 5.67, 6.0, 6.33 |

B vs A head to head: 0 wins, 23 losses, 1 ties (win rate 0.02). Grader agreement r = 0.8. Permutation test on run means: p = 0.029.

Builder cost: A 80675 tokens, 46.8 s; B 96752 tokens, 47.2 s per run. Dump: 200822 tokens reported for the main loop, 1612 s.

## t2-haiku

Prompt: a haiku about rare clouds

| arm | imagery | form | specificity | freshness | resonance | overall | per-run overall |
|---|---|---|---|---|---|---|---|
| A | 5.83 | 6.58 | 7.83 | 4.58 | 5.5 | **5.25** | 4.33, 5.33, 4.33, 7.0 |
| B | 7.83 | 9.0 | 7.25 | 7.42 | 7.0 | **7.5** | 8.67, 6.67, 8.0, 6.67 |

B vs A head to head: 20 wins, 2 losses, 2 ties (win rate 0.88). Grader agreement r = 0.76. Permutation test on run means: p = 0.086.

Builder cost: A 71542 tokens, 6.2 s; B 87373 tokens, 17.3 s per run. Dump: 213673 tokens reported for the main loop, 1586 s.

## t3-toast

Prompt: a dark mode, very compact collapsible toast UI menu for tracking a package

| arm | compact | collapsible | tracking | dark | usability | craft | overall | per-run overall |
|---|---|---|---|---|---|---|---|---|
| A | 7.25 | 7.58 | 7.75 | 8.08 | 6.67 | 7.42 | **7.33** | 7.33, 7.33, 8.33, 6.33 |
| B | 7.33 | 7.25 | 7.42 | 7.42 | 7.25 | 6.42 | **6.62** | 6.33, 6.67, 7.83, 5.67 |

B vs A head to head: 8 wins, 15 losses, 1 ties (win rate 0.35). Grader agreement r = 0.13. Permutation test on run means: p = 0.286.

Builder cost: A 77843 tokens, 27.0 s; B 99924 tokens, 42.1 s per run. Dump: 228261 tokens reported for the main loop, 1538 s.

