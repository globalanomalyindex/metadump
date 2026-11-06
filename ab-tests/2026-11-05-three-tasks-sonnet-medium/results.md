# A/B test 15 results: three tasks, Sonnet 5.5 at medium effort, metadump 0.10.0 (a hand, not the deck)

Arms: **A** = task only; **B** = task + a lite meta dump (test 13's Haiku-built dumps, re-finished with 0.10.0 and read with its use mode, which deals each session a hand). Builders and graders: Sonnet 5.5 at medium effort. Graders blind, 3 per block of 4.

## Summary

| task | A overall | B overall | B vs A win rate | p |
|---|---|---|---|---|
| t1-button | **7.83** | 6.42 | 0.08 | 0.057 |
| t2-haiku | 5.42 | **7.75** | 0.92 | 0.057 |
| t3-toast | 7.33 | 7.33 | 0.46 | 1.0 |

## t1-button

Prompt: a button with custom bezier curve hover state animations that makes it feel dreamlike and ethereal, but practical for a website

| arm | dreamlike | practical | motion | craft | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 8.25 | 7.08 | 7.83 | 7.92 | **7.83** | 7.33, 8.0, 8.0, 8.0 |
| B | 6.17 | 7.83 | 7.08 | 7.0 | **6.42** | 5.67, 7.33, 6.0, 6.67 |

B vs A head to head: 1 wins, 21 losses, 2 ties (win rate 0.08). Grader agreement r = 0.87. Permutation test on run means: p = 0.057.

Builder cost: A 76250 tokens, 36.6 s; B 104670 tokens, 61.1 s per run. Dump: 206192 tokens reported for the main loop, 1776 s.

## t2-haiku

Prompt: a haiku about rare clouds

| arm | imagery | form | specificity | freshness | resonance | overall | per-run overall |
|---|---|---|---|---|---|---|---|
| A | 5.92 | 6.67 | 7.67 | 4.58 | 5.0 | **5.42** | 6.33, 4.0, 6.0, 5.33 |
| B | 7.75 | 9.08 | 7.42 | 7.42 | 7.08 | **7.75** | 8.33, 8.33, 8.0, 6.33 |

B vs A head to head: 21 wins, 1 losses, 2 ties (win rate 0.92). Grader agreement r = 0.76. Permutation test on run means: p = 0.057.

Builder cost: A 71341 tokens, 8.0 s; B 95349 tokens, 29.5 s per run. Dump: 187177 tokens reported for the main loop, 1159 s.

## t3-toast

Prompt: a dark mode, very compact collapsible toast UI menu for tracking a package

| arm | compact | collapsible | tracking | dark | usability | craft | overall | per-run overall |
|---|---|---|---|---|---|---|---|---|
| A | 6.75 | 7.5 | 8.0 | 8.25 | 7.0 | 7.42 | **7.33** | 8.0, 7.33, 8.33, 5.67 |
| B | 7.83 | 7.92 | 7.08 | 7.92 | 8.08 | 7.5 | **7.33** | 7.67, 6.33, 8.0, 7.33 |

B vs A head to head: 8 wins, 10 losses, 6 ties (win rate 0.46). Grader agreement r = 0.74. Permutation test on run means: p = 1.0.

Builder cost: A 78177 tokens, 35.4 s; B 106810 tokens, 62.3 s per run. Dump: 216776 tokens reported for the main loop, 1426 s.

