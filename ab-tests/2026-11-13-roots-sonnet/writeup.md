# A/B test 23: the one-page roots skill against 0.13.0 and the prompt alone, Sonnet 5.5 at medium

The plugin started as one request to a model before a task: write out what you know as a structured JSON file, from the broad disciplines down to the specifics, then work from it. This test runs that idea as one page (`skill-roots/SKILL.md`) on test 22's two tasks. The builder writes its own dump in one pass, builds, checks and looks. There are no workers, no research, no verify, no deal and no finalize. A (prompt alone) and C (0.13.0 with the swarm's dump) are test 22's builds, graded again beside it. Pre-registration: `design.md`. Tables: `results.md`.

**The one page gets about 70% of the full system's gain for a small fraction of its cost.** It is behind 0.13.0, mostly in two places that are named below.

## Results

| task | A | C (0.13.0, swarm dump) | R (roots) | R vs C | R vs A | C vs A |
|---|---|---|---|---|---|---|
| lava lamp | 5.25 | **7.58** | 7.25 | 9–11–4 | 19–2–3 | 24–0–0 |
| basic calculator | 7.17 | **8.50** | 7.75 | 5–16–3 | 16–6–2 | 20–0–4 |

Pooled (won–lost–tied, stratified permutation test on run means):

- R vs A: 35–8–5, mean difference +1.29, p = 0.038.
- R vs C: 14–27–7, mean difference −0.54, p = 0.28.
- C vs A: 44–0–4, mean difference +1.83, p = 0.0004.

Grader agreement r = 0.93 and 0.77. All 24 builds work.

Spread and adherence, with the graders told what each task fixes and what it leaves open (second amendment in `design.md`):

| task | spread in what is open, A / C / R | builds of 4 that break what is fixed, A / C / R |
|---|---|---|
| lava lamp | 3.0 / 6.33 / 5.0 | 0.67 / 0 / 0 |
| basic calculator | 1.67 / 7.33 / 5.0 | 0 / 0 / 0.67 |

Scripted calculator checks passed, of nine: A 9, 9, 9, 9; C 9, 9, 9, 9; R 9, 9, 8, 9.

## Pre-registered hypotheses

1. **R beats A pooled and on each task. Yes:** 35–8–5, 19–2–3 and 16–6–2.
2. **R is within half a point of C on each task. On the lava lamp, yes (−0.33). On the calculator, no (−0.75).** The stronger form, that R does not lose to C pooled, fails: 14–27–7.
3. **R costs less. Yes.** Its builder used 98 and 84 thousand tokens against C's 126 and 108, in about the same time, and there was no dump to build (25 and 27 minutes, and about 2.6 million worker tokens for the calculator's).
4. **On the calculator, `basic` 7.5 or more, and as many scripted checks as A and C. No:** `basic` was 7.25 (C 8.58, A 8.92), and one build let a twelve-digit number run past its display.
5. **R's sets are less varied than C's. Yes:** 5.0 against 6.33 and 7.33. All eight R sessions built the classic kind, as the page tells a first session to.
6. **All 8 write the dump first in one write, and at least 6 look. Yes:** 8 and 8, after the amendment.

**What the result decides.** The design said: within half a point on both tasks, the one page becomes the proposal for the default; more than a point below on either, a middle path. The result falls between the two. The owner's decision (2026-11-13) was the middle path: the one page becomes quick mode, the lightest depth below `lite` and opt-in, and the full build stays the default (ADR 0021). Quick mode is this page with the two things below added.

## Where the one page lost

**"Basic."** One R calculator added a history panel and three added a full-width backspace bar. Graders: "the history panel is padded scope for a basic calculator". The page says a size word bounds the build, but it says so in the section on writing the dump. 0.13.0 says it as a step of building, and its dump lists what "basic" rules out (history, memory, scientific keys) as anti-keywords, written by a worker whose only job was exclusions.

**The floor.** C's eight builds scored between 7.0 and 8.67. R's ranged from 5.67 to 9.0, and R's best lava lamp was the best build in the test. Both weak lava lamps failed the same way: the wax "collapses into a pool" or "migrates to the top and stays there". Those two builders looked three and five times and read five and seven screenshots, and each look shows the page in its first seconds, before the wax has run down. One of these builders had written the right test in its own dump ("do blobs ever stall forever at the top or bottom") and had no way to run it. In test 22 all four of 0.12.0's lava lamps had the same fault.

So the gap is not the missing research or the missing workers as such. It is two specific things the swarm's dump happened to carry (what a size word excludes) or that no version checks (how a thing behaves after it has run a while).

## What the dumps looked like

Each R session wrote its dump first, in one write, in under a minute. They ran 1.4 to 2.5 thousand tokens, shorter than the 3 to 5 the page asks for. A typical one has four disciplines with principles, steps, tricks and tests; the thing's parts and three to five kinds; four areas of specifics with tiered keywords and value ranges; half a dozen anti-keywords; and four to eight checks. The lava lamp dumps wrote out the convection cycle, metaball rendering and the test for stalled wax from memory. The swarm's dumps were 31 thousand tokens each.

## The first round, set aside

The first eight roots builds are in `r0/`, ungraded (first amendment in `design.md`). Only three of those eight builders looked at what they made: the script sat outside the skill's folder, and the page mentioned the look in passing. With the scripts inside the skill and the look as its own numbered step, all eight looked. A step the page does not number gets skipped.

## Process

| | looks | images read |
|---|---|---|
| lava lamp, R | 4, 3, 5, 2 | 4, 5, 7, 4 |
| calculator, R | 4, 2, 2, 1 | 1, 0, 1, 1 |

## Cost

| task | A tokens / time | C tokens / time | R tokens / time | dump for C |
|---|---|---|---|---|
| lava lamp | 75k / 41 s | 126k / 3.2 min | 98k / 3.3 min | 197k for the main loop, 25 min, 21 agents |
| calculator | 73k / 25 s | 108k / 84 s | 84k / 101 s | 212k for the main loop, 27 min, 19 agents |

## Caveats

- A and C are the same sixteen files as in test 22; only R is new. n = 4 per arm per task, LLM graders, two tasks.
- The roots page was written after test 22's results on these tasks were known. It names neither task, but it was not written blind to them.
- R's dump and build come from one Sonnet session. C's dump was built by Haiku workers and read by Sonnet. R against C compares two whole pipelines.
- Each R session wrote its own dump. A dump kept and reused across sessions, with later sessions taking the next kind, was not tested.
- R against C is 14–27–7 with p = 0.28. The direction is clear in the head-to-heads; the size of the gap is not settled by eight builds.
- The owner's design hook fired inside builder sessions. It applies to every arm.
