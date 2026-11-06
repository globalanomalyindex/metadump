# A/B test 11 results: four example tasks, Haiku 5.5 at low effort for everything, metadump 0.7.1

Arms: **A** = task only; **B** = task + a lite meta dump (0.7.1). Builders, dump agents and graders: Haiku 5.5 at low effort. Graders blind, 3 per block of 4.

## Summary

| task | A overall | B overall | B vs A win rate | p |
|---|---|---|---|---|
| t1-button | 6.42 | **7.08** | 0.62 | 0.314 |
| t2-sandbox | 6.33 | **6.83** | 0.65 | 0.486 |
| t3-poem | 5.17 | **7.92** | 0.98 | 0.029 |
| t4-figma | **5.67** | 5.42 | 0.54 | 0.886 |

## t1-button

Prompt: a button with custom bezier curve hover state animations that makes it feel dreamlike and ethereal, but practical for a website

| arm | dreamlike | practical | motion | craft | overall | per-run overall |
|---|---|---|---|---|---|---|
| A | 7.0 | 6.08 | 6.67 | 6.83 | **6.42** | 6.0, 5.67, 6.33, 7.67 |
| B | 6.58 | 8.08 | 7.5 | 7.42 | **7.08** | 7.0, 8.0, 6.67, 6.67 |

B vs A head to head: 13 wins, 7 losses, 4 ties (win rate 0.62). Grader agreement r = 0.38. Permutation test on run means: p = 0.314.

Builder cost: A 85953 tokens, 53.7 s; B 114359 tokens, 78.7 s per run. Dump: 166357 tokens reported for the main loop, 626 s.

## t2-sandbox

Prompt: a 2D physics sandbox where you can drag boxes around

| arm | physics | interaction | stability | clarity | craft | overall | per-run overall |
|---|---|---|---|---|---|---|---|
| A | 5.92 | 6.67 | 6.67 | 7.75 | 6.25 | **6.33** | 7.0, 7.0, 6.0, 5.33 |
| B | 7.75 | 7.75 | 7.67 | 4.67 | 6.75 | **6.83** | 6.0, 6.67, 7.0, 7.67 |

B vs A head to head: 13 wins, 6 losses, 5 ties (win rate 0.65). Grader agreement r = 0.2. Permutation test on run means: p = 0.486.

Builder cost: A 85929 tokens, 54.9 s; B 144120 tokens, 196.6 s per run. Dump: 170227 tokens reported for the main loop, 681 s.

## t3-poem

Prompt: a short poem about rare clouds, ending with a question

| arm | imagery | specificity | question | freshness | resonance | overall | per-run overall |
|---|---|---|---|---|---|---|---|
| A | 5.83 | 7.0 | 4.92 | 4.33 | 4.92 | **5.17** | 5.33, 6.33, 4.67, 4.33 |
| B | 7.67 | 8.42 | 8.17 | 7.5 | 7.42 | **7.92** | 7.33, 7.67, 8.0, 8.67 |

B vs A head to head: 23 wins, 0 losses, 1 ties (win rate 0.98). Grader agreement r = 0.88. Permutation test on run means: p = 0.029.

Builder cost: A 69230 tokens, 7.8 s; B 91394 tokens, 21.1 s per run. Dump: 177846 tokens reported for the main loop, 724 s.

## t4-figma

Prompt: a 5 second looping animation in the style of Figma brand visuals

| arm | style | motion | loop | craft | originality | overall | per-run overall |
|---|---|---|---|---|---|---|---|
| A | 5.67 | 7.0 | 8.5 | 6.67 | 4.33 | **5.67** | 4.0, 6.33, 7.0, 5.33 |
| B | 6.17 | 5.92 | 8.08 | 5.75 | 4.83 | **5.42** | 7.33, 5.33, 5.33, 3.67 |

B vs A head to head: 12 wins, 10 losses, 2 ties (win rate 0.54). Grader agreement r = 0.53. Permutation test on run means: p = 0.886.

Builder cost: A 79029 tokens, 39.7 s; B 104569 tokens, 46.2 s per run. Dump: 179610 tokens reported for the main loop, 790 s.

## Pooled across the four tasks

- B scored higher on 3 of 4 tasks. The mean B−A gap is +0.92 points.
- An exact stratified permutation test gives p = 0.024, two-sided, over 24,010,000 relabelings within tasks (`pooled.py`, `pooled.json`).
- B won 61 of 96 blind head-to-heads, lost 23 and tied 12 (win rate 0.70).
- **The pooled result rests on the poem.** Without it, the other three tasks give a gap of +0.31 points and p = 0.45. They lean toward B, but that could be noise at n = 4.

## The pre-registered hypotheses

1. **B ≥ A on at least 3 of 4 tasks: met.** B was ahead on the button, sandbox and poem. On the Figma loop it was 0.25 behind.
2. **Dumps closer to the 8–15K token target than test 10's 30–47K: closer, still over.** The four dumps came in at 16.8K, 17.2K, 17.7K and 21.6K tokens.
3. **Fewer widening rounds than tests 9 and 10: not met.** Three dumps ran one widening round, as tests 8 and 9 did. The fourth (sandbox) was due one but its main loop stopped first. What changed is *why* rounds ran: constraint findings no longer trigger them. The button's verify logged 7 constraint findings and moved on. The rounds that did run came from quality, job and definition narrowings.

## What happened, task by task

**Button (B 7.08 vs A 6.42, win rate 0.62, p = 0.31).**
- B's lead is mostly practical (8.08 vs 6.08): focus states, reduced motion, cheap properties. Motion was 7.5 vs 6.67.
- A was a little more dreamlike (7.0 vs 6.58).
- Click tests were even. Every build handles reduced motion and uses custom curves (5.25 per build on average in both arms). In one build per arm (A-r3, B-r3) hovering the largest button changed nothing.
- B builders read the dump: 114K tokens and 79 s per run, against 86K and 54 s.

**Sandbox (B 6.83 vs A 6.33, win rate 0.65, p = 0.49).**
- B was clearly better on physics (7.75 vs 5.92), interaction (7.75 vs 6.67) and stability (7.67 vs 6.67).
- B was much worse on clarity (4.67 vs 7.75). The B builds showed fewer controls and less on-screen help; B-r1 has a single Reset button.
- All 8 builds pass the drag, fall and hook tests.
- Grader agreement was low (r = 0.20), so the gap is noisy.
- B builders took far longer: 197 s against 55 s, using the three runs that finished normally. B-r4's file was final after about 4 minutes, but its own Playwright self-check hung, and it reported 33 minutes. That run is left out of the time mean. The dump's two unresolved contradictions were about the drag joint.

**Poem (B 7.92 vs A 5.17, 23 wins, 0 losses, 1 tie, p = 0.029, the smallest possible at n = 4).**
- Graders agreed strongly (r = 0.88).
- B led every criterion. The biggest gains were the closing question (8.17 vs 4.92) and freshness (7.5 vs 4.33).
- All 8 poems end on a question.
- B's poems are shorter (59–73 words, against 58–107) and each holds one formation and its light.
- **All four B poems chose the same cloud: nacreous.** A's poems named a range (nacreous, noctilucent, lenticular, mammatus).
- That convergence traces to the dump. Its `llm_brief` "Core" line says to choose one formation, and nacreous comes first in its examples. The dump's own builder flagged that line as a possible narrowing, and verify didn't catch it. The graders didn't penalize the sameness, because each saw only four poems and never all eight together. It is the test-8 pattern (one reading gets copied) at the level of subject matter.

**Figma-style loop (A 5.67 vs B 5.42, win rate 0.54, p = 0.89).**
- **Every A build reproduced Figma's logo mark or came close.** All three graders flagged A-r1, A-r2 and A-r4 as rebuilding the five-shape mark in its brand colors. One of three flagged A-r3. **No B build used the logo.** This answers the pre-registered secondary question: the dump distilled the style without carrying logo copying into the builds.
- B scored higher on style (6.17 vs 5.67) and originality (4.83 vs 4.33).
- B lost on motion (5.92 vs 7.0) and craft (5.75 vs 6.67). B-r4's starburst is pinned to the top-left corner by a CSS transform that overrides its SVG translate, which drew a 3.67 run mean. Graders called B-r3's drift a generic screensaver.
- Three of the four B builds share motifs from the dump: a selection-handle square and a starburst.
- All 8 loops are periodic (seam difference 0.0 at 5 s).
- Post hoc, the dense frame check found sharper jumps in the A builds: the largest frame-to-frame change was 1.5–80× the median, against 1.2–5× for B. A's scatter-and-reassemble choreography causes some of that. It is descriptive, not a pre-registered outcome.

## The dumps

See `dumps.md` for each dump agent's report.
- Each dump was built by a Haiku-low main loop with 15–16 Haiku-low workers.
- Each took 10.4–13.2 minutes of main-loop time, using 166–180K main-loop tokens (worker usage not included).
- Grounding was 20–30% collected.
- No dump held a finished deliverable.
- The new `quote_not_in_page` check ran against the page cache for 31 quoted sources (8, 11, 9 and 3 per dump) and flagged none.
- The Figma dump has no hex palette, because no fetched source gave one, and records that as an open question rather than guessing.

## Harness deviations

- **First Figma grading round voided.** The capture script loaded each frame sheet as one `data:` URL, and ten full-size frames went past Chrome's 2 MB URL limit. Seven of the eight loop sheets rendered blank, and the graders said so. The sheet is now written to a temp file. The Figma task was recaptured, re-blinded with the same label orders and regraded by six fresh graders. The voided judgments are in `t4-figma/judgments-void/` and not counted.
- **Post-hoc loop measure.** `max_jump_ratio` was added to the Figma capture after the first round (see above). The pre-registered seam metric is unchanged.
- **Poem cards.** The showcase cards were first re-flowing long verse lines. They now keep each writer's line breaks and shrink the type to fit instead. Graders read the markdown, so their scores are unaffected.

## Caveats

- n = 4 per arm per task, one dump per task, and Haiku graders at low effort judging motion and physics from frames and source.
- The sandbox dump skipped the widening round it was due.
- Featured runs (run 1 of each arm) were chosen before grading. That is why the Figma showcase shows A-r1, a logo rebuild, beside B-r1.
- "Figma brand visuals" names a real brand. Graders judged style resemblance; nothing here is Figma's own work.
