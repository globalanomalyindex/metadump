# A/B test 9 results (rerun of test 8 after ADR 0010): three "sticky and punchy" bezier curves as loops, metadump 0.7.0 (facets), Haiku everything

Arms: **A** = task only; **B** = task + metadump 0.7.0 with ADR 0010 (lite)

## Blind grader scores (0-10; 4 runs per arm x 3 graders = 12 scores per arm)

| arm | overall | sticky | punchy | distinct | presentation | craft | mean rank (1-4) | overall per run |
|---|---|---|---|---|---|---|---|---|
| A | **4.5** | 5.42 | 6.0 | 6.0 | 3.67 | 4.17 | 3.5 | 5.0, 4.0, 4.33, 4.67 |
| B | **7.67** | 7.0 | 7.0 | 7.08 | 8.5 | 7.67 | 1.5 | 8.33, 7.0, 8.0, 7.33 |

## Head to head (same grader, same block, overall)

- **B vs A**: 24 wins, 0 losses, 0 ties (win rate 1.0)

Grader agreement: mean pairwise Pearson r = 0.96.

## Does it work? (headless Chrome: window.CURVES valid, loops animate, animations use the declared curves, 390 px)

| arm | works | CURVES valid | animating | uses declared curves | no overflow at 390 px | JS errors |
|---|---|---|---|---|---|---|
| A | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 | 0 |
| B | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 | 0 |

## Cost per build run (Haiku)

| arm | runs | mean tokens | mean seconds | mean tool calls |
|---|---|---|---|---|
| A | 4 | 76425 | 23.8 | 3 |
| B | 4 | 131799 | 117.5 | 13 |

Dump build (one-off, Haiku main loop plus Haiku workers): 212746 tokens reported for the main loop, 1560 s.

Exact two-sided permutation test on run means: B − A = +3.16, p = 0.029 (2 of 70). That is the smallest p possible with 4 runs per arm: every B run scored above every A run.

## Curve diversity (`diversity.py`, from `window.CURVES`)

| | test 8 A | test 8 B | test 9 A | test 9 B |
|---|---|---|---|---|
| distinct curves among the arm's 12 | 10 | 4 | 11 | **12** |
| mean distance between a build's three curves | 0.249 | 0.036 | 0.276 | **0.208** |
| curves copied from the dump | – | 11 of 12 | – | **0 of 12** |

Distance is the mean absolute difference between two curves' progress over 101 time samples (0 means identical).

## What happened

- **The fixes worked.**
  - None of B's 12 curves is copied from the dump. Each build composed its own set from the quality readings: a slow-start grip, an overshoot catch, and a hard stop or fast press, often framed as press, release and settle (the dump's default scope reading).
  - Within-build spread went from 0.036 to 0.208. Only B-r2 stayed tight (0.075), and its graders said so ("Plant and Snap are both ease-out shapes").
  - Two A builds reached for the common easeOutBack preset `(0.34, 1.56, 0.64, 1)`, which B avoided.
- **B won on every criterion, including the ones it lost or tied in test 8:**
  - distinct 7.08 vs 6.0 (test 8: 3.83 vs 6.67);
  - sticky 7.0 vs 5.42 (test 8: tied);
  - punchy 7.0 vs 6.0 (test 8: tied);
  - presentation 8.5 vs 3.67, and craft 7.67 vs 4.17.

  Graders agreed closely (r = 0.96), and B won all 24 head-to-head pairs.
- **What the B builds share:** a graph per curve with a playhead, live progress and peak or settle readouts, a reference curve, a pause control, reduced motion handled (most start paused), and loops with explicit hold and return phases, so the grip visibly lingers. Graders called B-r3's shared 1.6 s clock "the most clearly distinct" set.
- **What A did:** bare ball-on-track loops with the spec string as the only readout. A had no graphs and mostly no pause or reduced-motion handling; A-r1's graphs and dots clip. A-r1 also had the most grip-like single curve (an undershoot anticipation).
- **B's flaws:**
  - B-r2's two ease-outs are too similar;
  - B-r4's Pause/Play breaks under reduced motion (a CSS media rule keeps the animation paused);
  - small dot overflow in B-r1.
- **The dump:**
  - Size: 94 entries, about 32.7K tokens (test 8: 52.8K). The index is 9.5K of that, down from 25K.
  - Grounding: 26% collected, from 9 hosts.
  - Quality readings: sticky has four, punchy has three, with no default.
  - The "write the curves" route leads with the quality facets and decision points. No entry, export or default holds a finished set.
  - Verify's definition and copy passes both fired in round 1: the default reading could be pasted as a full plan, and the quality facets read as definitions. That set off a widening round, and verify re-ran afterwards.
  - Still open after widening: some pool exemplars are published presets, which pull against "custom". The B builds didn't use them.
  - Warnings: 5 `wordy_entry` and 6 `oversized_entry`.
- **Two build defects:**
  - Synthesis reported two `open_questions` defaults, but none reached the built file.
  - The moodboard entries lacked tier and provenance until a repair shard fixed them.

  The build agent also added `*/metadumps/.work/` to `ab-tests/.gitignore`, which is correct.
- **Cost:**
  - dump: 26 minutes, 20 Haiku agents;
  - B builds: 132K tokens and 118 s each, against 76K and 24 s for A.

## Hypothesis check

- B's distinct score at least 5.5 and close to A's: **met** (7.08, above A's 6.0).
- B keeps its presentation and craft lead: **met** (8.5 vs 3.67, 7.67 vs 4.17).
- B ≥ A overall: **met** (7.67 vs 4.50, win rate 1.0, p = 0.029).
- At least 8 distinct tuples among B's 12 curves: **met** (12).
- Quality facets for both words with at least two readings, and no finished set: **met** (4 and 3 readings; no set).

## Caveats

- A scored lower than in test 8 (4.50 vs 6.11 for test 8's working A builds), and the graders differ, so part of the gap is this A arm. B beat every A build in both blocks, though, and its distinctness rose on the objective measure, not only in grades.
- n = 4 per arm, one task, LLM graders, and one dump build.
