# A/B test 14 results: three tasks, Haiku 5.5 at medium effort for everything, metadump 0.9.0 (the deal)

Arms: **A** = task only; **B** = task + a lite meta dump (test 13's 0.8.1 dumps, read with 0.9.0 use mode and the deal). Builders, dump agents and graders: Haiku 5.5 at medium effort. Graders blind, 3 per block of 4.

## Summary

| task | A overall | B overall | B vs A win rate | p |
|---|---|---|---|---|
| t1-button | 6.75 | **7.0** | 0.56 | 0.686 |
| t2-haiku | **7.0** | 6.5 | 0.48 | 0.657 |
| t3-toast | 6.5 | **8.08** | 0.92 | 0.029 |

## t1-button

Prompt: a button with custom bezier curve hover state animations that makes it feel dreamlike and ethereal, but practical for a website

| arm | dreamlike | practical | motion | craft | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 7.0 | 6.08 | 6.75 | 7.33 | **6.75** | 7.33, 6.33, 5.67, 7.67 |
| B | 6.33 | 8.17 | 7.33 | 7.17 | **7.0** | 8.0, 6.67, 6.67, 6.67 |

B vs A head to head: 11 wins, 8 losses, 5 ties (win rate 0.56). Grader agreement r = 0.29. Permutation test on run means: p = 0.686.

Builder cost: A 91347 tokens, 82.4 s; B 165859 tokens, 198.9 s per run. Dump: 206192 tokens reported for the main loop, 1776 s.

## t2-haiku

Prompt: a haiku about rare clouds

| arm | imagery | form | specificity | freshness | resonance | overall | per-run overall |
|---|---|---|---|---|---|---|---|
| A | 6.5 | 9.08 | 8.25 | 5.75 | 6.42 | **7.0** | 6.0, 6.0, 8.33, 7.67 |
| B | 7.08 | 7.08 | 7.67 | 6.67 | 6.83 | **6.5** | 7.0, 8.0, 6.33, 4.67 |

B vs A head to head: 11 wins, 12 losses, 1 ties (win rate 0.48). Grader agreement r = 0.86. Permutation test on run means: p = 0.657.

Builder cost: A 67950 tokens, 7.5 s; B 115274 tokens, 19.0 s per run. Dump: 187177 tokens reported for the main loop, 1159 s.

## t3-toast

Prompt: a dark mode, very compact collapsible toast UI menu for tracking a package

| arm | compact | collapsible | tracking | dark | usability | craft | overall | per-run overall |
|---|---|---|---|---|---|---|---|---|
| A | 6.58 | 5.67 | 7.83 | 7.92 | 6.58 | 6.83 | **6.5** | 7.0, 6.67, 6.33, 6.0 |
| B | 7.75 | 8.5 | 8.17 | 8.33 | 8.33 | 7.92 | **8.08** | 8.67, 7.33, 8.33, 8.0 |

B vs A head to head: 21 wins, 1 losses, 2 ties (win rate 0.92). Grader agreement r = 0.75. Permutation test on run means: p = 0.029.

Builder cost: A 88836 tokens, 65.2 s; B 157628 tokens, 191.6 s per run. Dump: 216776 tokens reported for the main loop, 1426 s.

