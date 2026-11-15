# A/B test 22: 0.13.0 on two tasks no version has seen (2026-11-13)

Pre-registered before any dump or build ran. Tests 20 and 21 left three things open:

- Test 21's fix for the timer (a size word bounds the build) was shown only on the task it was written from.
- 0.13.0 lost the snow globe twice. Test 21 traced it to the dump's angles being ways of photographing a snow globe, and 0.13.0 now asks for angles that are kinds of the thing, with the home angle (the kind a stranger pictures) first and dealt first (ADR 0019, "What test 21 found"). That change has never been built from.
- The look's playing checks (ADR 0020) have had nothing to catch: neither a timer nor a snow globe has much behaviour to break.

So this test uses two new tasks, one of each kind, and builds everything fresh.

**Tasks.** Chosen by Claude before anything ran.

1. **visual:** "a lava lamp". A drawn object with motion, the same class as the snow globe, where 0.13.0 lost.
2. **technical:** "a basic calculator". It has a size word, and behaviour that can be wrong in ways a walk or a scripted play can see.

No 0.13.0 text or code was written against these tasks. The synthesis brief's examples are a pomodoro timer and a snow globe.

**Arms.** 4 fresh builds per arm per task, Sonnet 5.5 at medium effort.
- **A:** the task alone.
- **B:** the task plus the dump, used the way 0.12.0's SKILL.md describes (`git archive 9d9a54e skills/metadump`, in `skill-prev/`): independent deals, a look that renders and hovers.
- **C:** the task plus the dump, used the way 0.13.0's SKILL.md describes (the working tree, frozen for the test): deals that rotate through a ledger starting from the home angle, a look that plays the page, a size word that bounds the build.

**Dumps.** One per task, built fresh at lite depth by 0.13.0's create mode: a Haiku 5.5 main loop at medium effort and Haiku workers, plain subagents, no Workflow, as in tests 19 and 20. No references. B and C read the same entries: the work dir is finalized twice, by 0.13.0 for C (`metadumps/`) and by 0.12.0 for B (`prev/metadumps/`). So the new angle rule reaches both dump arms, and C against B measures use mode only: the order of the deal, the look, the size-word rule and the hand's wording. The dump is used as create mode leaves it. Its angles are recorded before any build and not edited.

**Prompts.** The harness wording of tests 13 to 21 (`prompts.py`). Each build is one self-contained HTML file.

**Grading.** As tests 20 and 21: blind Sonnet 5.5 graders at medium effort, two blocks of six per task (runs 1–2 and 3–4 of each arm), three graders per block with the same fixed label orders (`blind.py`); three variety graders per task over sets P, Q and R (`variety.py`).

**What graders see.**
- lava lamp: desktop and phone at rest; a strip of frames untouched at 0, 2, 4 and 6 s, then after a click on the lamp, then after its first control is pressed; the source.
- calculator: desktop and phone at rest; a strip of a scripted use (12 + 7 =, 0.1 + 0.2 =, 8 ÷ 0 =, the 9 key twenty times, clear); the source.

**Rubrics (0 to 10 each).**
- lava lamp: likeness (unmistakably a lava lamp: a glass vessel on a base with a cap, blobs of wax in liquid, lit from below); visuals; motion (wax that rises, stretches, merges, splits and sinks believably, slow and organic); presentation; overall.
- calculator: basic (a basic calculator, complete and not overbuilt); correctness; usability; craft; code; overall.

**Scripted checks on the calculator** (`capture.py`, the same steps for every arm; a count out of 9, no grader involved):
1. 12 + 7 = shows 19.
2. 9 × 8 = shows 72.
3. 7 − 10 = shows −3.
4. 0.1 + 0.2 = shows 0.3 (and not 0.30000000000000004).
5. 2 + 3 × 4 = shows 14 or 20 (either convention).
6. 8 ÷ 0 = shows something other than NaN, undefined or nothing, and after clear 1 + 1 = shows 2.
7. The 9 key pressed twenty times: the number stays inside the display.
8. Clear returns the display to 0 or empty.
9. Typed on the keyboard, 4 * 5 Enter shows 20.

**Measures.** Quality per task and pooled for each pair of arms (head-to-heads within a grader's block; an exact stratified permutation test on run means); variety per set; the angle each dump session was dealt and its deal number; whether each dump builder dealt, looked, ran a scripted play and read images; which findings the look printed and whether the build changed after; what 0.13.0's look reports on every finished build of every arm (`lookall.py`); the scripted checks; for the lava lamp, whether it moves untouched; tokens and time.

**Hypotheses.**
1. C ≥ B overall on both tasks, or at least C does not lose to B pooled (wins ≥ losses).
2. C beats A pooled (more wins than losses), and on each task.
3. C's four sessions start from four different angles, the first deal from the dump's first angle, and C's variety ≥ B's on both tasks.
4. On the lava lamp, the class of task 0.13.0 lost twice: C does not lose to B head to head (wins ≥ losses), and C's `likeness` is 7.5 or more.
5. Both dumps list kinds of the thing with the home angle first, and no shots (read by Claude before any build, and by the angle pass in verify).
6. On the calculator, C's `basic` is at or above B's and not more than half a point below A's.
7. On the calculator, C's builds pass at least as many scripted checks as B's and as A's (mean per build).
8. At least 3 of the 4 C calculator builders run a scripted play, and 0.13.0's look reports no more findings from playing on C's finished builds than on B's.

Any other result is reported as is.

**Confounds.**
- n = 4 per arm per task; one dump per task, built by Haiku while the builders are Sonnet; LLM graders.
- The tasks were chosen by the same model that built 0.13.0, and the lava lamp was chosen for being like the snow globe.
- B reads a dump built by 0.13.0's create mode, so B is 0.12.0's use mode and not 0.12.0 end to end. If the new angle rule helps, it helps B too.
- B's deals are independent, so B may draw the home angle more than once or not at all. Which angles each arm built is reported.
- A has no look. C against A is "dump plus deal plus look" against "prompt alone".
- The scripted checks need to find the display and the keys on pages nobody has seen. Where the script can't find them, the check is recorded as not run, not as failed, and the build is checked by hand.

## Amendment, made before any calculator build with the dump started

When the calculator dump finished, a deal ledger already sat beside it (`.deals/basic-calculator.deals.json`, written nine minutes before the final build). One of create mode's verify workers had dealt the dump for its dry run, as use mode tells any consumer to. That one deal took the home angle, "keypad on a card", so the first real session would have started from the second angle, and C's four sessions would never have built the home angle.

This is a defect in 0.13.0 as it stood, found by this test: a dry run during the build must not spend the rotation. The fix (verify deals with `--no-ledger`, and create mode hands over a dump with no ledger) is made after this test's builds, since the skill is frozen until then. For the test the stray ledger was moved to `t2-calculator/stray-ledger/` before any build, so C's deals start at 1, which is what the fixed skill does. The lava lamp dump had no ledger. Nothing else was touched.
