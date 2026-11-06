# A/B test 18 results: three tasks, Sonnet 5.5 at medium effort, metadump 0.12.0 (0.11.0 plus the look)

Arms: **A** = task only; **B** = task + a lite meta dump (test 16's 0.11.0 dumps, re-finished with 0.12.0 so their reading steps end with the look, read with 0.12.0's use mode: the deal first, the look last). Builders and graders: Sonnet 5.5 at medium effort; A is test 16's prompt-only builds, reused. Graders blind, 3 per block of 4.

## Summary

| task | A overall | B overall | B vs A win rate | p |
|---|---|---|---|---|
| t1-button | 6.5 | **8.25** | 0.98 | 0.029 |
| t2-haiku | 5.08 | **8.0** | 0.96 | 0.029 |
| t3-toast | 6.83 | **7.5** | 0.58 | 0.514 |

## t1-button

Prompt: a button with custom bezier curve hover state animations that makes it feel dreamlike and ethereal, but practical for a website

| arm | dreamlike | practical | motion | craft | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 6.83 | 7.08 | 7.0 | 7.17 | **6.5** | 6.0, 7.0, 7.0, 6.0 |
| B | 8.42 | 8.08 | 8.33 | 8.08 | **8.25** | 8.0, 8.0, 9.0, 8.0 |

B vs A head to head: 23 wins, 0 losses, 1 ties (win rate 0.98). Grader agreement r = 0.9. Permutation test on run means: p = 0.029.

Builder cost: A 76250 tokens, 36.6 s; B 111883 tokens, 80.4 s per run. Dump: 221751 tokens reported for the main loop, 1959 s.

## t2-haiku

Prompt: a haiku about rare clouds

| arm | imagery | form | specificity | freshness | resonance | overall | per-run overall |
|---|---|---|---|---|---|---|---|
| A | 5.58 | 7.25 | 7.08 | 4.5 | 4.92 | **5.08** | 6.33, 4.33, 4.67, 5.0 |
| B | 7.75 | 9.08 | 7.75 | 7.58 | 7.92 | **8.0** | 7.67, 8.33, 9.0, 7.0 |

B vs A head to head: 23 wins, 1 losses, 0 ties (win rate 0.96). Grader agreement r = 0.85. Permutation test on run means: p = 0.029.

Builder cost: A 71341 tokens, 8.0 s; B 97182 tokens, 25.2 s per run. Dump: 221383 tokens reported for the main loop, 1613 s.

## t3-toast

Prompt: a dark mode, very compact collapsible toast UI menu for tracking a package

| arm | compact | collapsible | tracking | dark | usability | craft | overall | per-run overall |
|---|---|---|---|---|---|---|---|---|
| A | 7.58 | 7.33 | 7.5 | 7.83 | 6.58 | 7.0 | **6.83** | 8.0, 7.0, 7.33, 5.0 |
| B | 7.08 | 7.83 | 8.08 | 7.83 | 7.83 | 7.58 | **7.5** | 7.33, 6.67, 8.33, 7.67 |

B vs A head to head: 11 wins, 7 losses, 6 ties (win rate 0.58). Grader agreement r = 0.79. Permutation test on run means: p = 0.514.

Builder cost: A 78177 tokens, 35.4 s; B 113085 tokens, 90.1 s per run. Dump: 190509 tokens reported for the main loop, 1578 s.

