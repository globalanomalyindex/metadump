# A/B test 22 results: 0.13.0 against 0.12.0 and the prompt alone, two held-out tasks, Sonnet 5.5 at medium effort

Arms: **A** = task only; **B** = task + a lite meta dump, read with 0.12.0's use mode; **C** = task + the same dump, read with 0.13.0's use mode (deals rotate from the home angle, the look plays the page). Dumps built fresh by 0.13.0's create mode (Haiku 5.5 swarm). Builders and graders: Sonnet 5.5 at medium effort, all arms fresh. Graders blind, 3 per block of 6.

## Summary

| task | A | B (0.12.0) | C (0.13.0) | C vs B | C vs A | B vs A |
|---|---|---|---|---|---|---|
| t1-lavalamp | 5.08 | 6.17 | **8.0** | 21–0–3 | 24–0–0 | 16–4–4 |
| t2-calculator | 6.83 | 7.42 | **8.17** | 17–6–1 | 22–2–0 | 12–4–8 |

## t1-lavalamp

Prompt: a lava lamp

| arm | likeness | visuals | motion | presentation | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 5.92 | 4.92 | 5.42 | 5.83 | **5.08** | 5.67, 5.0, 3.67, 6.0 |
| B | 6.75 | 7.5 | 4.83 | 7.33 | **6.17** | 5.33, 7.33, 5.33, 6.67 |
| C | 8.58 | 8.08 | 7.25 | 7.67 | **8.0** | 9.0, 8.0, 8.0, 7.0 |

C vs B head to head: 21 wins, 0 losses, 3 ties (win rate 0.94); permutation test on run means p = 0.057.
C vs A head to head: 24 wins, 0 losses, 0 ties (win rate 1.0); permutation test on run means p = 0.029.
B vs A head to head: 16 wins, 4 losses, 4 ties (win rate 0.75); permutation test on run means p = 0.229.

Grader agreement r = 0.95.

Builder cost per run: A 75246 tokens, 40.9 s; B 123964 tokens, 177.6 s; C 126001 tokens, 192.6 s. Dump: 196987 tokens reported for the main loop, 1484 s.

## t2-calculator

Prompt: a basic calculator

| arm | basic | correctness | usability | craft | code | overall | per-run overall |
|---|---|---|---|---|---|---|---|
| A | 8.5 | 7.75 | 7.0 | 6.67 | 8.08 | **6.83** | 6.67, 7.0, 7.0, 6.67 |
| B | 6.58 | 8.25 | 8.0 | 8.42 | 5.75 | **7.42** | 8.67, 6.67, 6.67, 7.67 |
| C | 8.25 | 8.58 | 8.25 | 8.42 | 7.25 | **8.17** | 8.33, 7.33, 8.67, 8.33 |

C vs B head to head: 17 wins, 6 losses, 1 ties (win rate 0.73); permutation test on run means p = 0.257.
C vs A head to head: 22 wins, 2 losses, 0 ties (win rate 0.92); permutation test on run means p = 0.029.
B vs A head to head: 12 wins, 4 losses, 8 ties (win rate 0.67); permutation test on run means p = 0.429.

Grader agreement r = 0.65.

Builder cost per run: A 73485 tokens, 24.5 s; B 109821 tokens, 80.5 s; C 108470 tokens, 84.3 s. Dump: 212391 tokens reported for the main loop, 1595 s.

