# A/B test 16 results: three tasks, Sonnet 5.5 at medium effort, metadump 0.11.0 (amplify the user's words), dumps rebuilt

Arms: **A** = task only; **B** = task + a lite meta dump (rebuilt with 0.11.0 by the Haiku swarm at medium effort, read with its use mode and the deal; A is test 15's prompt-only builds, reused). Builders and graders: Sonnet 5.5 at medium effort. Graders blind, 3 per block of 4.

## Summary

| task | A overall | B overall | B vs A win rate | p |
|---|---|---|---|---|
| t1-button | **7.5** | 7.33 | 0.44 | 1.0 |
| t2-haiku | 5.33 | **7.0** | 0.75 | 0.114 |
| t3-toast | **7.96** | 5.83 | 0.06 | 0.029 |

## t1-button

Prompt: a button with custom bezier curve hover state animations that makes it feel dreamlike and ethereal, but practical for a website

| arm | dreamlike | practical | motion | craft | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 7.92 | 7.0 | 7.75 | 7.83 | **7.5** | 6.33, 8.67, 7.33, 7.67 |
| B | 6.33 | 8.25 | 7.08 | 7.83 | **7.33** | 7.67, 6.33, 6.33, 9.0 |

B vs A head to head: 9 wins, 12 losses, 3 ties (win rate 0.44). Grader agreement r = 0.79. Permutation test on run means: p = 1.0.

Builder cost: A 76250 tokens, 36.6 s; B 105799 tokens, 65.1 s per run. Dump: 221751 tokens reported for the main loop, 1959 s.

## t2-haiku

Prompt: a haiku about rare clouds

| arm | imagery | form | specificity | freshness | resonance | overall | per-run overall |
|---|---|---|---|---|---|---|---|
| A | 6.0 | 7.33 | 7.58 | 4.58 | 4.92 | **5.33** | 5.67, 4.0, 6.0, 5.67 |
| B | 7.08 | 9.0 | 6.08 | 7.25 | 7.08 | **7.0** | 8.0, 7.67, 8.0, 4.33 |

B vs A head to head: 18 wins, 6 losses, 0 ties (win rate 0.75). Grader agreement r = 0.89. Permutation test on run means: p = 0.114.

Builder cost: A 71341 tokens, 8.0 s; B 96091 tokens, 24.7 s per run. Dump: 221383 tokens reported for the main loop, 1613 s.

## t3-toast

Prompt: a dark mode, very compact collapsible toast UI menu for tracking a package

| arm | compact | collapsible | tracking | dark | usability | craft | overall | per-run overall |
|---|---|---|---|---|---|---|---|---|
| A | 7.75 | 7.67 | 8.08 | 8.25 | 6.92 | 7.83 | **7.96** | 8.17, 7.33, 9.0, 7.33 |
| B | 6.5 | 7.0 | 7.0 | 7.0 | 6.25 | 5.17 | **5.83** | 6.67, 5.33, 6.33, 5.0 |

B vs A head to head: 0 wins, 21 losses, 3 ties (win rate 0.06). Grader agreement r = 0.91. Permutation test on run means: p = 0.029.

Builder cost: A 78177 tokens, 35.4 s; B 108928 tokens, 64.9 s per run. Dump: 190509 tokens reported for the main loop, 1578 s.

