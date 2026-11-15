# Confirmation test results: metadump 1.0.0, frozen before the tasks were known, Sonnet 5.5 at medium effort (the full-evidence pass of amendment 1, not the registered grades)

Arms: **A** = task only; **F** = task + a lite meta dump built by the frozen skill's swarm, read with its use mode; **Q** = task + quick mode (the builder writes its own dump in one pass). Tasks named by the owner after the freeze. Builders and graders: Sonnet 5.5 at medium effort, all fresh. Graders blind, 3 per block of 6.

## Summary

| task | A | F (full build) | Q (quick) | F vs A | Q vs A | F vs Q |
|---|---|---|---|---|---|---|
| t1-pelican | 7.25 | **8.08** | 7.25 | 16–4–4 | 7–7–10 | 15–3–6 |
| t2-ascii | 6.0 | 7.33 | **8.08** | 17–1–6 | 22–1–1 | 4–16–4 |
| t3-bento | 7.46 | **8.25** | 7.25 | 15–3–6 | 8–14–2 | 13–6–5 |
| t4-blocks | 5.79 | 6.94 | **8.56** | 20–0–4 | 24–0–0 | 0–21–3 |

## t1-pelican

Prompt: an SVG animation of a pelican riding a bike

| arm | fidelity | correctness | craft | usability | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 8.17 | 7.5 | 7.17 | 7.67 | **7.25** | 6.67, 7.67, 8.0, 6.67 |
| F | 8.25 | 8.25 | 8.08 | 8.25 | **8.08** | 7.67, 8.67, 9.0, 7.0 |
| Q | 8.17 | 7.42 | 7.08 | 7.33 | **7.25** | 7.33, 7.0, 7.0, 7.67 |

F vs A head to head: 16 wins, 4 losses, 4 ties (win rate 0.75); permutation test on run means p = 0.257.
Q vs A head to head: 7 wins, 7 losses, 10 ties (win rate 0.5); permutation test on run means p = 1.0.
F vs Q head to head: 15 wins, 3 losses, 6 ties (win rate 0.75); permutation test on run means p = 0.257.

Grader agreement r = 0.65.

Builder cost per run: A 81796 tokens, 52.8 s; F 121750 tokens, 120.8 s; Q 91606 tokens, 105.0 s. Dump: 203576 tokens reported for the main loop, 1195 s.

## t2-ascii

Prompt: a simple interactive ascii color mixing engine

| arm | fidelity | correctness | craft | usability | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 6.83 | 6.83 | 5.92 | 5.92 | **6.0** | 5.0, 7.0, 6.0, 6.0 |
| F | 7.67 | 8.08 | 7.17 | 7.58 | **7.33** | 8.0, 7.0, 6.67, 7.67 |
| Q | 8.42 | 7.92 | 8.17 | 7.67 | **8.08** | 8.67, 7.0, 8.33, 8.33 |

F vs A head to head: 17 wins, 1 losses, 6 ties (win rate 0.83); permutation test on run means p = 0.086.
Q vs A head to head: 22 wins, 1 losses, 1 ties (win rate 0.94); permutation test on run means p = 0.057.
F vs Q head to head: 4 wins, 16 losses, 4 ties (win rate 0.25); permutation test on run means p = 0.2.

Grader agreement r = 0.75.

Builder cost per run: A 81383 tokens, 46.9 s; F 112259 tokens, 114.5 s; Q 94170 tokens, 247.1 s. Dump: 195020 tokens reported for the main loop, 1157 s.

## t3-bento

Prompt: a bento box-inspired collapsible UI menu component for a fictional coffee company site

| arm | fidelity | correctness | craft | usability | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 7.58 | 7.33 | 7.5 | 7.17 | **7.46** | 8.0, 7.5, 6.0, 8.33 |
| F | 8.42 | 8.0 | 8.33 | 7.5 | **8.25** | 8.33, 9.33, 7.67, 7.67 |
| Q | 7.92 | 8.17 | 7.08 | 7.83 | **7.25** | 6.83, 5.83, 8.33, 8.0 |

F vs A head to head: 15 wins, 3 losses, 6 ties (win rate 0.75); permutation test on run means p = 0.343.
Q vs A head to head: 8 wins, 14 losses, 2 ties (win rate 0.38); permutation test on run means p = 0.829.
F vs Q head to head: 13 wins, 6 losses, 5 ties (win rate 0.65); permutation test on run means p = 0.257.

Grader agreement r = 0.75.

Builder cost per run: A 82606 tokens, 53.5 s; F 124265 tokens, 130.1 s; Q 92673 tokens, 140.6 s. Dump: 212344 tokens reported for the main loop, 2412 s.

## t4-blocks

Prompt: a simple block-building sandbox game with a 32x32 block world

| arm | fidelity | correctness | craft | usability | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 6.67 | 7.17 | 5.25 | 6.17 | **5.79** | 6.67, 6.0, 5.0, 5.5 |
| F | 6.92 | 8.0 | 7.08 | 7.58 | **6.94** | 7.67, 7.33, 6.17, 6.6 |
| Q | 8.83 | 8.25 | 8.67 | 7.92 | **8.56** | 9.33, 8.0, 8.0, 8.9 |

F vs A head to head: 20 wins, 0 losses, 4 ties (win rate 0.92); permutation test on run means p = 0.086.
Q vs A head to head: 24 wins, 0 losses, 0 ties (win rate 1.0); permutation test on run means p = 0.029.
F vs Q head to head: 0 wins, 21 losses, 3 ties (win rate 0.06); permutation test on run means p = 0.029.

Grader agreement r = 0.93.

Builder cost per run: A 77161 tokens, 21.5 s; F 112908 tokens, 69.9 s; Q 88725 tokens, 100.9 s. Dump: 202236 tokens reported for the main loop, 1286 s.

