# A/B test 22: 0.13.0 on two tasks no version had seen, Sonnet 5.5 at medium

Three arms on two new tasks, "a lava lamp" and "a basic calculator": the prompt alone (A), the dump read with 0.12.0's use mode (B), and the same dump read with 0.13.0's (C). 0.13.0 here is the version after test 21: angles are kinds of the thing, the home angle is dealt first, a size word bounds the build, the look plays the page. Pre-registration: `design.md`. Tables: `results.md`. All twelve builds per task side by side: `t1-lavalamp/overview.png`, `t2-calculator/overview.png`.

**0.13.0 beat both arms on both tasks.** Its lava lamps were more alike than 0.12.0's, and more like lava lamps.

## Results

| task | A | B (0.12.0) | C (0.13.0) | C vs B | C vs A | B vs A | variety A / B / C |
|---|---|---|---|---|---|---|---|
| lava lamp | 5.08 | 6.17 | **8.00** | 21–0–3 | 24–0–0 | 16–4–4 | 2.0 / **8.0** / 5.33 |
| basic calculator | 6.83 | 7.42 | **8.17** | 17–6–1 | 22–2–0 | 12–4–8 | 1.0 / 5.0 / **5.33** |

Pooled (won–lost–tied, stratified permutation test on run means):

- C vs B: 38–6–4, mean difference +1.29, p = 0.016.
- C vs A: 46–2–0, mean difference +2.12, p = 0.0004.
- B vs A: 28–8–12, mean difference +0.83, p = 0.09.

Grader agreement r = 0.95 and 0.65. All 24 builds work, and all 12 calculators pass all nine scripted checks.

## Pre-registered hypotheses

1. **C ≥ B on both tasks. Yes**, and 38–6–4 pooled.
2. **C beats A pooled and on each task. Yes:** 24–0–0 and 22–2–0.
3. **Four sessions, four angles, the first deal from the home angle, and C's variety ≥ B's on both tasks. The deal: yes. Variety: no on the lava lamp** (5.33 against 8.0; all three variety graders picked B). Yes on the calculator, narrowly (5.33 against 5.0).
4. **On the lava lamp, C does not lose to B and its `likeness` is 7.5 or more. Yes:** 21–0–3, and 8.58.
5. **Both dumps list kinds with the home angle first and no shots. Yes.** The lava lamp's first draft had two shot-style angles, and the angle pass in verify replaced them. The calculator's five are a card keypad, a pocket handheld, a dark glass panel, a flat phone keypad and a light web card.
6. **On the calculator, C's `basic` is at or above B's and within half a point of A's. Yes:** 8.25 against B's 6.58 and A's 8.5.
7. **C passes at least as many scripted checks as B and A. A tie at the ceiling:** every build in every arm passes nine of nine. The checks measured nothing.
8. **At least three C calculator builders run a scripted play, and the look reports no more playing findings on C than on B. Yes:** all four ran plays (4, 2, 6 and 1), and the look's playing findings were 0 per build for C and 0.25 for B on the lava lamp, 0 for both on the calculator.

## What made the difference

**The lava lamp.** B's independent deals gave "squat round lamp" to three of four sessions.

| angle | B | C |
|---|---|---|
| classic tapered bottle (home) | | 9.00 |
| rounded globe | | 8.00 |
| silver hourglass base | 6.67 | 8.00 |
| tall tapered violet lamp | | 7.00 |
| squat round lamp | 5.33, 7.33, 5.33 | |

- Two of B's squat lamps "read more like a fishbowl or potion flask". C's sessions were dealt the first four angles in order, starting from the classic bottle, which scored 9.0: "the most convincing classic lava lamp".
- On the one angle both arms built, C scored 8.0 and B 6.67.
- The largest gap was motion: 7.25 against 4.83. In all four B builds the wax "stays a low pool", "barely moves" or "hangs at the top". In three of C's it "stretches, detaches and sinks". Nothing in the transcripts shows why. One guess is that 0.13.0's look shows the page some seconds after load, when a slow start is visible, and 0.12.0's shows it at rest.

**The calculator.** B drew the pocket handheld twice, and both came out as seven-segment skeuomorphs that graders called "overbuilt for basic". C's four sessions took four kinds, the home keypad among them.

- `basic` was 8.25 for C and 6.58 for B, and `code` 7.25 against 5.75. This is the size-word rule from test 21, now on a task it wasn't written from.
- On the three angles both arms built, C was ahead by about half a point (8.67 and 8.67, 8.33 and 7.67, 7.33 and 6.67).

**So C's lead has three parts that this test cannot separate:** the home angle and a spread of angles in place of a collision, the size-word rule, and the look. B's collision on the lava lamp is the same mechanism that favoured B on the snow globe in test 20, where its sessions happened to draw the two safest angles. Rotation removes that luck in both directions.

## Variety

On the lava lamp B's set was more varied: a fishbowl globe, a violet lamp, an amber egg, a chrome lamp on a shelf. C's was "two near-identical tall rocket lamps plus one bulbous lamp". Two things explain it.

- Three of the dump's five kinds share one silhouette: the classic taper, the same taper on a silver base, the same taper in violet. Verify had flagged the violet lamp as a colour cast on the home angle.
- 0.12.0 tells a session to go wherever its angle leads. Its three "squat round lamp" sessions went three different ways, and two of them left the lava lamp behind.

Kinds are narrower than the treatments 0.13.0 first asked for (tests 20 and 21: variety 5.33 to 8.33, with quality down). On these two tasks 0.13.0 sits at 5.33 on both, against 1.0 and 2.0 for the prompt alone.

**The variety score is not higher-is-better** (the owner's point, 2026-11-13). The variety graders reward any difference between builds, including one that breaks what the thing is. B's 8.0 on the lava lamp includes two builds graders said read as a fishbowl, and B's `likeness` was 6.75 against C's 8.58. Where a task has rules or standards, builds agreeing on them is the benefit: every calculator in every arm uses the same key layout and passes the same nine checks, and nobody would want four different arithmetics. Hypothesis 3 was written as if more spread were always better, and it is recorded above as it was written. From the next test on, each task says in advance what is fixed and what is open, adherence is measured directly, and variety graders are asked which differences break what the task requires.

## What the playing checks did

As in tests 20 and 21, nothing was there to catch. No arm shipped a behaviour bug, and the prompt-only calculators pass every scripted check too.

- All four C calculator builders ran the dump's review questions as plays (0.1 + 0.2, 8 ÷ 0 with `expect Error`), and every expectation held.
- The look led to one real fix: a display clipping 3 px of its digits (C-r3).
- Two builders wrote play selectors the shell mangled, and the look said so.

A calculator at this level is not a task where Sonnet breaks behaviour. The playing checks are still supported only by the 32 past builds in ADR 0020.

## A defect the test found

When the calculator dump finished, a deal ledger already sat beside it. A verify worker had dealt the dump for its dry run nine minutes before the final build, and that deal took the home angle. The first real session would have started from the second angle. The ledger was set aside before any build (see the amendment in `design.md`). The skill now clears a ledger when a dump is built from its work folder, keeps it when a write-back re-finishes a dump, and tells verify workers not to deal (two tests in `tests/test_finalize.py`).

## Process

| | looks | images read | scripted plays |
|---|---|---|---|
| lava lamp, B | 4, 2, 5, 2 | 13, 2, 4, 2 | not available |
| lava lamp, C | 3, 5, 4, 2 | 6, 8, 7, 5 | 0 |
| calculator, B | 2, 4, 2, 1 | 0, 2, 1, 1 | not available |
| calculator, C | 2, 2, 3, 1 | 1, 2, 0, 0 | 4, 2, 6, 1 |

Every dump builder dealt and looked.

## Cost

| task | A tokens / time | B tokens / time | C tokens / time | dump |
|---|---|---|---|---|
| lava lamp | 75k / 41 s | 124k / 3.0 min | 126k / 3.2 min | 197k for the main loop, 25 min, 21 agents |
| calculator | 73k / 25 s | 110k / 81 s | 108k / 84 s | 212k for the main loop, 27 min, 19 agents |

The calculator's main loop reported about 2.6 million tokens across its workers. Both dumps came out near 31 thousand tokens, twice lite's target.

## Caveats

- n = 4 per arm per task, one dump per task, LLM graders. Two tasks.
- The tasks were chosen by Claude, and the lava lamp was chosen for being like the snow globe.
- B reads a dump built by 0.13.0's create mode, so B is 0.12.0's use mode and not 0.12.0 end to end.
- B's draw on the lava lamp was unlucky (one angle three times). That is what independent deals do, but with one round per arm the size of C's lead there owes something to it.
- The by-angle tables are post hoc with one to three builds per cell.
- The scripted checks first misread three calculators that draw seven-segment digits with no text. The script was changed to read what those displays announce to screen readers, and the three were rerun; the checks themselves did not change.
- The owner's design hook fired inside at least one builder session. It applies to every arm.
