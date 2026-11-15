# A/B test 20: 0.13.0 against 0.12.0 and the prompt alone, Sonnet 5.5 at medium

Three arms on three new tasks: the prompt alone (A), the dump read with 0.12.0's use mode (B), and the same dump read with 0.13.0's use mode (C), where deals rotate (ADR 0019) and the look plays the page (ADR 0020). Pre-registration: `design.md`. Tables: `results.md`.

**0.13.0 as first built made sessions much more varied and made the two HTML tasks worse.** It is not shipped in that form. Test 21 (`../2026-11-12-revision-sonnet/`) tests the revision this led to.

## Results

| task | A | B (0.12.0) | C (0.13.0) | C vs B | C vs A | B vs A | variety A / B / C |
|---|---|---|---|---|---|---|---|
| field guide entry | 5.17 | 7.83 | **7.92** | 11–10–3 | 24–0–0 | 24–0–0 | 1.0 / 3.67 / **5.33** |
| pomodoro timer | 7.08 | **7.79** | 6.71 | 5–17–2 | 7–12–5 | 16–6–2 | 1.33 / 4.67 / **8.33** |
| snow globe | 7.42 | **7.58** | 5.92 | 1–19–4 | 2–18–4 | 11–9–4 | 2.0 / 4.0 / **8.33** |

Pooled (won–lost–tied, stratified permutation test on run means):

- C vs B: 17–46–9, mean difference −0.89, p = 0.07.
- C vs A: 33–30–9, p = 0.58.
- B vs A: 51–15–6, p = 0.02. This repeats tests 18 and 19 on a third set of tasks.

Grader agreement r = 0.95, 0.78, 0.84. Every one of the nine variety graders called C's set the most varied.

## Pre-registered hypotheses

1. **C ≥ B on at least 2 of 3 tasks, and C wins more than it loses against B pooled. No.** C was level on the field guide and lost the timer and the snow globe.
2. **C wins more than it loses against A pooled. Barely: 33–30–9**, and it lost both HTML tasks to A.
3. **C's sessions start from four different angles, and C's variety ≥ B's on at least 2 of 3. Yes, on all three.** C was dealt four different angles on every task. B's independent deals gave 3, 4 and 2 different angles.
4. **All 12 C builders deal, and at least 7 of the 8 HTML builders run the look. Yes: 12 of 12 and 8 of 8.** One 0.12.0 timer builder never looked.
5. **C's finished HTML builds carry fewer findings from the look's playing checks than B's. Not testable here.** 0.13.0's look found no playing defect in any timer of any arm, and two in one B snow globe. These tasks had nothing of that kind to catch. At rest it found the fewest in C (0.25 and 1.0 per build, against B's 0.5 and 2.5 and A's 1.5 and 1.75).
6. **On the timer, C's `simple` is not below A's. No:** 5.75 against 8.25. B's was 6.5.
7. **On the field guide C and B differ in variety and not in quality. Yes.**

## Why C lost

The graders' notes put every C loss on the angle the session was dealt.

**Snow globe.** The dump's angles were "close-up dome", "shelf in a room", "scene-only dome", "abstract globe" and "single-figure bubble". Overall score by angle:

| angle | B | C |
|---|---|---|
| close-up dome | 8.67, 8.33 | 6.33 |
| shelf in a room | 6.67, 6.67 | 7.00 |
| scene-only dome | | 5.67 |
| abstract globe | | 4.67 |

- "Scene-only dome" has no base: "it reads as a glass ball on a table" (all three graders).
- "Abstract globe" has no scene: "a crystal ball more than a snow globe".
- "Shelf in a room" makes the globe small in every arm that built it.
- On "close-up dome", B's two builds stayed classic, and C's became a fisheye city that was "less obviously a snow globe".

Likeness was 6.08 for C against 8.33 for B and 8.42 for A.

**Timer.** The angles were six faces for the timer. C drew "count as the face" (5.67: "the giant pomodoro-count numeral outranks the actual countdown") and "quiet text-only status" (5.83, a terminal look; B's build of the same angle scored 5.33). B drew "bare big number" (8.83), which C did not. On the three angles both arms drew, B averaged 7.44 and C 7.06. All four C timers and two B timers were called overbuilt: saved state, confirm steps, notifications, settings.

So three causes, all of them 0.13.0's own:

1. **The synthesis brief asked for the wrong kind of angle.** 0.13.0 told dumps to write angles as "different finished things a stranger could tell apart". The dumps did that by removing or demoting what makes the thing itself: the base, the scene, the clock. An angle should vary what the request leaves open and keep what the request names.
2. **Use mode told sessions to take their angle far.** The hand said the further a session took its angle the more ground the sessions covered. On the one snow globe angle with builds in both arms, C's went furthest and scored lowest.
3. **Rotation makes every angle count.** Deals that rotate build every angle. Independent deals build them by chance, and B's four snow globe sessions drew only the two safest (about a 3% draw). A session meets a weak angle equally often either way, so in expectation rotation costs nothing, but it turns a weak angle from a risk into a certainty within one round.

Two more things the transcripts show:

- **The sheet replaced reading.** On the snow globe, B's builders ran the look 2 to 5 times and opened 1 to 7 full-size screenshots. C's ran it 1 to 3 times and opened 1 to 3 images, mostly the sheet.
- **Both dump arms inflate a size word.** `simple` was 8.25 for the prompt alone, 6.5 for B and 5.75 for C. The dumps' worn paths each point at one more feature ("state lost on reload", "silent reset"), and builders added them.

## What held up

- **Rotation does what it was built for.** Four sessions, four angles, on every task; variety 5.33, 8.33 and 8.33 against 3.67, 4.67 and 4.0.
- **Sessions follow their angle**, in both arms, which is why the angle's quality decides the build's.
- **The dump still beats the prompt alone under 0.12.0** (51–15–6), and on the field guide by 24–0–0 in both dump arms: the prompt-only entries were "one entry written four times".
- **The look's playing checks found nothing to fix on these tasks**, so this test says nothing for or against them. Their evidence remains the 32 pages of tests 18 and 19 (ADR 0020).

## What changed because of it

Recorded in ADRs 0019 and 0020 and tested in test 21:

- an angle is a different treatment that keeps everything the request names, and verify has an angle pass;
- the hand and use mode say the angle sets the treatment and the request stays the user's;
- a size word in the request bounds the build;
- the look tells the builder to read the full-size shots, and the sheet is an overview.

## Process notes

- The snow globe ledger already held one deal when C's builders started: a verify worker had dealt during the dump build, from an earlier angle list. C's sessions were deals 2 to 5 and still got four different angles.
- One 0.12.0 timer (B-r4) fails the scripted reset: it asks for a second press.

## Cost

| task | A tokens / time | B tokens / time | C tokens / time | dump |
|---|---|---|---|---|
| field guide | 73k / 31 s | 112k / 65 s | 107k / 58 s | 193k for the main loop, 15 min, 13 agents |
| timer | 74k / 26 s | 107k / 72 s | 112k / 95 s | 220k, 21 min, 19 agents |
| snow globe | 86k / 84 s | 127k / 3.5 min | 138k / 4.7 min | 206k, 25 min, 22 agents |

## Caveats

- n = 4 per arm per task, one dump per task, LLM graders.
- The tasks were chosen by Claude, before any run.
- The by-angle comparison above is post hoc and rests on one to two builds per cell.
- B and C read the same dump, built by 0.13.0's create mode, so B is 0.12.0's use mode and not 0.12.0 end to end.
