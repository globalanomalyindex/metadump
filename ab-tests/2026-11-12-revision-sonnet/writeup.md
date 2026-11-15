# A/B test 21: the revised 0.13.0 on the two tasks where it lost, Sonnet 5.5 at medium

Test 20 found 0.13.0's sessions more varied than 0.12.0's and worse on both HTML tasks. This test reruns those two tasks with the revision that followed (an angle keeps everything the request names, the hand no longer pushes sessions out, a size word bounds the build, builders read the full-size shots). A and B are test 20's own builds, graded again; D is four fresh builds per task. Pre-registration: `design.md`. Tables: `results.md`.

**The revision fixed the timer and did not fix the snow globe.** 0.13.0 is still not shown to be better than 0.12.0 on quality. It is more varied on every task so far.

## Results

| task | A | B (0.12.0) | D (0.13.0 revised) | D vs B | D vs A | B vs A | variety A / B / D |
|---|---|---|---|---|---|---|---|
| pomodoro timer | 6.25 | 7.21 | **7.54** | 15–6–3 | 18–6–0 | 18–4–2 | 1.0 / 5.33 / **6.67** |
| snow globe | 7.08 | **7.25** | 6.08 | 3–20–1 | 7–17–0 | 9–11–4 | 2.33 / 4.67 / **5.67** |

Pooled (won–lost–tied, stratified permutation test on run means):

- D vs B: 18–26–4, mean difference −0.42, p = 0.60.
- D vs A: 25–23–0, mean difference +0.15, p = 0.87.
- B vs A: 27–15–6, p = 0.38.

Grader agreement r = 0.92 and 0.81. All 24 builds work.

## Pre-registered hypotheses

1. **D ≥ B on both tasks, or at least no pooled loss. No.** Yes on the timer, no on the snow globe, and 18–26–4 pooled.
2. **D beats A pooled. By two decisions (25–23), which is a tie.** It won the timer 18–6 and lost the snow globe 7–17.
3. **D's variety is above B's on both tasks. Yes:** 6.67 against 5.33, and 5.67 against 4.67. Five of the six variety graders called D's set the most varied and one called a tie.
4. **Four sessions, four angles, on both tasks. Yes.**
5. **On the timer, `simple` at or above 6.5. Yes: 8.17**, against 5.67 for B and 7.25 for A in this grading.
6. **On the snow globe, `likeness` at or above 7.5. No: 7.42.** That is up from 6.08, and below B's 7.92 and A's 7.83.

## The timer

Three of D's four timers scored 8.5 or more ("full-bleed phase colour" 8.67, "held between phases" 8.5, "ring that fills over the session" 9.0). The size word did what it was meant to: `simple` rose from 5.67 to 8.17 and `code` from 5.75 to 7.33, with `correctness` the highest of the three arms.

The fourth, "quiet text-only status", scored 4.0. One inherited CSS rule (`font-size: inherit` on the heading that holds the clock) shrank the countdown to body-text size. The builder ran the look twice and read three screenshots. Nothing in the look asks whether the thing the request names is the main thing on the page.

## The snow globe

Every D build is now recognisably a snow globe with a base and a scene. They lost on how they were drawn.

| angle | B | C (test 20) | D |
|---|---|---|---|
| close-up dome | 7.33, 8.67 | 6.33 | 6.67 |
| shelf in a room | 5.67, 7.33 | 7.00 | 6.00 |
| one colour family | | | 6.33 |
| long exposure streaks | | | 5.33 |

(B and D as graded here; C as graded in test 20.)

- "Long exposure streaks" opens on a pale blue dome with the snow settled and a "Long exposure: off" button. Graders: "empty at rest", "the white snow barely shows against it".
- "One colour family" is blue on blue: "the scene is dim and flat", "the cabin is washed out".
- "Shelf in a room" put a chapel in a blurred room, and "the snow haze washes out the scene". This angle has averaged about 6.4 in every arm that built it.
- "Close-up dome" is a sound globe with "a black angular base" and controls cropped below the fold.

Across tests 20 and 21, none of 0.13.0's eight snow globes scored above 7.0. Five of the eight prompt-only and 0.12.0 globes scored 7.33 or more (Fisher's exact test, p ≈ 0.03). Those five are the same picture: a night dome, a lit cabin, dense snow in the air, a wood or brass base.

**What the rewritten angles are.** The dump was built from photographs and videos of snow globes, and its angles describe photographs: a tight frame, a view from across a room, one colour cast, a long exposure. The angle pass checked that each kept the dome, the base, the scene and the shake, and they do. But none of them is a kind of snow globe anyone makes. Each is a way of shooting the same cabin globe, so each session drew the classic globe through a handicap, and the scene barely changed ("the cabin is constant", in all three arms).

The timer's angles are different in kind. A ring that fills, a full-bleed phase colour and a bare big number are timers people design and ship. Those angles scored 8.5 to 9.0. So did the field guide's in test 20 (a taxonomic record, a field plate, a scholar's file).

**Rotation shows the average angle.** A round of four sessions now builds four different angles, so only one of them can start from the strongest. B's four snow globe sessions drew the two most classic angles twice each. In expectation rotation changes nothing; in one round it means the arm's score is the mean of its angles, and three of the snow globe's four were weaker than the plain globe.

## What this changes

- **An angle is a kind of the thing, not a way of showing it.** A kind someone would make: a different scene or subject, style, era or material. Not a camera position, a lighting effect or a moment caught.
- **The first angle is the home angle,** the kind a stranger pictures, and the first deal from a dump starts there. Later deals rotate outward. Someone who builds once gets the classic with the dump's material; someone who builds again gets a different kind.
- Still open: a check for "the thing the request names is the main thing on the page" (the shrunken clock).

Both are untested here. Test 22 checks them on a task no version has seen.

## Process

| | looks | images read | scripted plays | findings |
|---|---|---|---|---|
| timer | 1, 2, 2, 3 | 0, 3, 0, 1 | 0 | none |
| snow globe | 3, 2, 3, 1 | 6, 2, 3, 2 | 2, 0, 1, 0 | `focus-static` and `hover-static` on one first look, fixed by the second |

Builders dealt on all eight runs and looked on all eight. Nobody opened the sheet. As in test 20, the look's playing checks had nothing to catch on these two tasks.

## Cost

| task | A tokens / time | B tokens / time | D tokens / time |
|---|---|---|---|
| timer | 74k / 26 s | 107k / 72 s | 109k / 74 s |
| snow globe | 86k / 84 s | 127k / 3.5 min | 120k / 2.8 min |

## Caveats

- **In-sample.** These are the tasks the revision was written from. The revised use mode's own text cites test 20's snow globe and timer as examples, so D's builders read a description of the failure they were being tested on. That can only have helped D.
- n = 4 per arm per task, one dump per task, LLM graders. A's four snow globes, built from one identical prompt, range from 4.67 to 8.67.
- A and B are the same eight files as in test 20, so B's lucky draw of angles is carried over, not repeated.
- The by-angle table is post hoc, with one or two builds per cell and C graded in a different session.
- The first set of snow globe grades was cut off by a usage limit. One resumed grader reported skipping the phone screenshots and the source, so all nine were discarded (`t3-snowglobe/discarded-resumed/`) and nine fresh graders ran.
- The snow globe's angles needed one repair round after the angle pass failed four of five (see the amendment in `design.md`).
