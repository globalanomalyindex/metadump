# A/B test 21: the revised 0.13.0 on the two tasks where test 20's 0.13.0 lost (2026-11-12)

Pre-registered before any revised build ran. Test 20 (`../2026-11-12-three-arms-sonnet/writeup.md`) found 0.13.0's sessions far more varied than 0.12.0's and worse on both HTML tasks (pooled 17–46–9 against 0.12.0). The graders' notes traced every loss to the angle a session was dealt:

- 0.13.0's synthesis brief asked for angles that are "different finished things", and the dumps wrote angles that removed defining parts: a snow globe with no base ("scene-only dome"), one with no scene ("abstract globe"), a timer whose session count is bigger than its clock ("count as the face").
- 0.13.0's use mode told each session to take its angle far. On the one snow globe angle both arms drew, 0.12.0's builds stayed classic (8.67, 8.33) and 0.13.0's became a fisheye city (6.33).
- Deals that rotate cover every angle, so a weak angle is sure to be built. Independent deals cover them only by chance, and 0.12.0's four snow globe sessions drew just the two safest.
- Both dump arms overbuilt against "simple" (0.12.0 6.5, 0.13.0 5.75, prompt alone 8.25).
- On the visual task 0.13.0's builders read 1 to 3 images (the sheet) where 0.12.0's read 1 to 7 full-size shots.

The revision (same working tree, still unreleased): an angle is a different treatment that keeps everything the request names, checked by a new angle pass in verify; the hand and use mode say the angle sets the treatment and the request stays the user's; a size word bounds the build; the look tells the builder to read the full-size shots and treats the sheet as an overview. Rotation and the look's playing checks are unchanged.

**This test is in-sample.** It asks whether those were the causes, on the tasks where they were found. It cannot show the revision generalises; a new task has to.

**Tasks:** "a simple pomodoro timer" and "a snow globe", as in test 20.

**Arms.**
- **A** (prompt alone) and **B** (0.12.0's use mode on test 20's dump): test 20's own builds, copied unchanged. B's snow globe sessions drew the two safest angles, so B is a strong baseline.
- **D:** 4 fresh builds per task, Sonnet 5.5 at medium effort, with the revised use mode on test 20's dump after one change: `essence.angles` rewritten by one Haiku 5.5 worker at medium effort following the corrected synthesis brief. The worker is given the brief and the dump, not test 20's results (the brief itself cites test 20's failed angles as examples). Everything else in the dump is byte-identical. The deal ledger starts empty.

**Grading.** As test 20: blind Sonnet 5.5 graders at medium effort, two blocks of six per task (runs 1–2 and 3–4 of A, B and D), three graders per block, the same label orders; three variety graders per task over sets P, Q, R. All grading is fresh, so A and B are scored again alongside D. Same rubrics and capture script.

**Hypotheses.**
1. D ≥ B overall on both tasks, or at least D does not lose to B pooled (wins ≥ losses).
2. D beats A pooled (more wins than losses), as the dump arm did in tests 18 and 19.
3. D's variety is above B's on both tasks.
4. D's four sessions start from four different angles on both tasks.
5. On the timer, D's `simple` score is at or above B's (6.5 in test 20).
6. On the snow globe, D's `likeness` is at or above 7.5 (0.13.0 scored 6.08).

Any other result is reported as is.

**Confounds.**
- In-sample, as above. n = 4 per arm per task; LLM graders.
- D differs from test 20's C in four ways at once (angles, wording, size-word rule, how the look's output is read), so this test can say whether the bundle works and not which part did.
- B read the dump with its original angles; D reads it with rewritten ones. D against B is "revised system" against "0.12.0 as it ran".

## Amendment, made before any D snow globe build started

The first rewrite of the snow globe's angles included a motionless still, which drops a step of the user's job (shake it and watch it settle). The revised system has a check for that, the angle pass in verify, so it was run as create mode would run it: one Haiku worker ran the angle pass on each dump, and where it failed angles, one Haiku gap worker rewrote them. The timer's six angles all passed. Four of the snow globe's five failed (the still, two that describe no motion, and "shelf in a room" for making the globe a small object among others) and were rewritten once. Lite allows one such round, so the result was not verified again. The lists and findings are in `<task>/repair/`. D's dumps hold the angles in `repair/angles.json`.
