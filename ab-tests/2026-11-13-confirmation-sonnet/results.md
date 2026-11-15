# Confirmation test results: metadump 1.0.0, frozen before the tasks were known, Sonnet 5.5 at medium effort

Arms: **A** = task only; **F** = task + a lite meta dump built by the frozen skill's swarm, read with its use mode; **Q** = task + quick mode (the builder writes its own dump in one pass). Tasks named by the owner after the freeze. Builders and graders: Sonnet 5.5 at medium effort, all fresh. Graders blind, 3 per block of 6.

## Summary

| task | A | F (full build) | Q (quick) | F vs A | Q vs A | F vs Q |
|---|---|---|---|---|---|---|
| t1-pelican | 7.17 | **8.17** | 7.25 | 15–3–6 | 10–8–6 | 17–4–3 |
| t2-ascii | 5.67 | 7.08 | **7.92** | 19–1–4 | 22–2–0 | 4–17–3 |
| t3-bento | **7.5** | 7.17 | 6.82 | 5–14–5 | 9–15–0 | 13–9–2 |
| t4-blocks | 5.92 | 6.17 | **8.75** | 10–5–9 | 24–0–0 | 0–24–0 |

## t1-pelican

Prompt: an SVG animation of a pelican riding a bike

| arm | fidelity | correctness | craft | usability | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 8.08 | 7.08 | 7.17 | 7.33 | **7.17** | 6.33, 7.33, 8.0, 7.0 |
| F | 8.5 | 7.92 | 8.25 | 8.08 | **8.17** | 8.67, 8.33, 8.67, 7.0 |
| Q | 8.08 | 7.25 | 7.17 | 7.17 | **7.25** | 6.67, 7.33, 7.0, 8.0 |

F vs A head to head: 15 wins, 3 losses, 6 ties (win rate 0.75); permutation test on run means p = 0.143.
Q vs A head to head: 10 wins, 8 losses, 6 ties (win rate 0.54); permutation test on run means p = 0.943.
F vs Q head to head: 17 wins, 4 losses, 3 ties (win rate 0.77); permutation test on run means p = 0.143.

Grader agreement r = 0.64.

Builder cost per run: A 81796 tokens, 52.8 s; F 121750 tokens, 120.8 s; Q 91606 tokens, 105.0 s. Dump: 203576 tokens reported for the main loop, 1195 s.

## t2-ascii

Prompt: a simple interactive ascii color mixing engine

| arm | fidelity | correctness | craft | usability | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 7.0 | 6.42 | 5.67 | 5.83 | **5.67** | 4.67, 6.67, 5.67, 5.67 |
| F | 7.25 | 7.83 | 7.0 | 7.25 | **7.08** | 7.67, 6.67, 6.67, 7.33 |
| Q | 8.33 | 7.75 | 8.0 | 7.5 | **7.92** | 8.67, 6.33, 8.67, 8.0 |

F vs A head to head: 19 wins, 1 losses, 4 ties (win rate 0.88); permutation test on run means p = 0.086.
Q vs A head to head: 22 wins, 2 losses, 0 ties (win rate 0.92); permutation test on run means p = 0.057.
F vs Q head to head: 4 wins, 17 losses, 3 ties (win rate 0.23); permutation test on run means p = 0.286.

Grader agreement r = 0.89.

Builder cost per run: A 81383 tokens, 46.9 s; F 112259 tokens, 114.5 s; Q 94170 tokens, 247.1 s. Dump: 195020 tokens reported for the main loop, 1157 s.

## t3-bento

Prompt: a bento box-inspired collapsible UI menu component for a fictional coffee company site

| arm | fidelity | correctness | craft | usability | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 7.83 | 7.33 | 7.58 | 7.08 | **7.5** | 8.33, 7.33, 6.83, 7.5 |
| F | 7.42 | 7.42 | 7.75 | 6.67 | **7.17** | 7.33, 8.0, 6.5, 6.83 |
| Q | 7.17 | 7.0 | 6.75 | 7.0 | **6.82** | 5.67, 5.67, 8.6, 7.33 |

F vs A head to head: 5 wins, 14 losses, 5 ties (win rate 0.31); permutation test on run means p = 0.543.
Q vs A head to head: 9 wins, 15 losses, 0 ties (win rate 0.38); permutation test on run means p = 0.429.
F vs Q head to head: 13 wins, 9 losses, 2 ties (win rate 0.58); permutation test on run means p = 0.686.

Grader agreement r = 0.59.

Builder cost per run: A 82606 tokens, 53.5 s; F 124265 tokens, 130.1 s; Q 92673 tokens, 140.6 s. Dump: 212344 tokens reported for the main loop, 2412 s.

## t4-blocks

Prompt: a simple block-building sandbox game with a 32x32 block world

| arm | fidelity | correctness | craft | usability | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 6.92 | 7.42 | 5.42 | 6.67 | **5.92** | 7.0, 6.0, 5.67, 5.0 |
| F | 6.83 | 7.67 | 6.42 | 6.83 | **6.17** | 6.67, 6.33, 6.0, 5.67 |
| Q | 8.75 | 8.42 | 8.75 | 8.0 | **8.75** | 9.33, 8.0, 8.33, 9.33 |

F vs A head to head: 10 wins, 5 losses, 9 ties (win rate 0.6); permutation test on run means p = 0.743.
Q vs A head to head: 24 wins, 0 losses, 0 ties (win rate 1.0); permutation test on run means p = 0.029.
F vs Q head to head: 0 wins, 24 losses, 0 ties (win rate 0.0); permutation test on run means p = 0.029.

Grader agreement r = 0.92.

Builder cost per run: A 77161 tokens, 21.5 s; F 112908 tokens, 69.9 s; Q 88725 tokens, 100.9 s. Dump: 202236 tokens reported for the main loop, 1286 s.

