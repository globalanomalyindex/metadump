# A/B test 24: the confirmation test of metadump 1.0.0, Sonnet 5.5 at medium

Tests 1 to 23 were run by the person designing the plugin on tasks that person chose. This one froze the skill first (33 files, by hash), took four tasks from the owner afterwards, and fixed the arms, the capture, the rubric and the analysis before any task was known. Three arms, four builds each per task: **A** the prompt alone, **Q** quick mode (the builder writes its own dump in one pass), **F** the full build (a `lite` dump from the swarm, read with use mode). Pre-registration: `design.md`, with one amendment written before any score was read. Tables: `results.md` (the registered grades), `results-full.md` (the second grading pass), `pooled.json`, `pooled-full.json`, `variety.json`, `process.json`, `grader-audit.json`. Pictures: `<task>/overview.png`, the twelve builds of a task side by side with both scores.

**Quick mode is confirmed. The full build is not, by this test's own rule.** On the registered grades quick mode beat the prompt alone by 1.12 points of 10 over the four tasks (65–25–6 head to head, p = 0.012, under the 0.025 the design set for each primary comparison). The full build beat it by 0.58 (49–23–24, p = 0.036): the right direction, and short of the threshold. Three things belong beside those two numbers.

- **Quick mode's result leans on task 4,** the one task whose wording was the assistant's suggestion and not the owner's alone. On the owner's three tasks quick mode is +0.55 (p = 0.23) and the full build +0.70 (p = 0.042).
- **On the bento menu the registered graders put both dump arms below the prompt alone:** 7.17 and 6.82 against 7.50.
- **The graders were not opening everything.** An audit of their transcripts, made before any score was read, found they opened four fifths of the pictures and read none of the sources (amendment 1). A second pass by graders who opened every file puts the full build at +1.03 (68–8–20, p = 0.0008) and quick mode at +1.16 (61–22–13, p = 0.0045). The amendment said in advance that a difference only the second pass shows is found after the fact, not confirmed. So the full build's result stays "not confirmed", with a stronger second reading beside it.

Nothing else on the design's list of what would count against the version happened. No arm broke what a task fixes. All 16 quick builders wrote their dump first, and all 16 looked.

## Results

Overall score, 0 to 10, mean of four builds and three graders. The registered grades are the primary analysis.

| task | A | F (full build) | Q (quick) | F vs A | Q vs A | F vs Q |
|---|---|---|---|---|---|---|
| 1. pelican on a bike (SVG animation) | 7.17 | **8.17** | 7.25 | 15–3–6 | 10–8–6 | 17–4–3 |
| 2. ASCII colour mixing engine | 5.67 | 7.08 | **7.92** | 19–1–4 | 22–2–0 | 4–17–3 |
| 3. bento menu for a coffee company | **7.50** | 7.17 | 6.82 | 5–14–5 | 9–15–0 | 13–9–2 |
| 4. block-building sandbox, 32×32 | 5.92 | 6.17 | **8.75** | 10–5–9 | 24–0–0 | 0–24–0 |
| mean | 6.56 | 7.15 | **7.69** | | | |

The same builds, graded again by graders who opened every picture and read every source (amendment 1):

| task | A | F (full build) | Q (quick) | F vs A | Q vs A | F vs Q |
|---|---|---|---|---|---|---|
| 1. pelican | 7.25 | **8.08** | 7.25 | 16–4–4 | 7–7–10 | 15–3–6 |
| 2. ASCII | 6.00 | 7.33 | **8.08** | 17–1–6 | 22–1–1 | 4–16–4 |
| 3. bento | 7.46 | **8.25** | 7.25 | 15–3–6 | 8–14–2 | 13–6–5 |
| 4. blocks | 5.79 | 6.94 | **8.56** | 20–0–4 | 24–0–0 | 0–21–3 |
| mean | 6.62 | 7.65 | **7.79** | | | |

Pooled over tasks: head-to-heads within a grader's block, and an exact stratified permutation test on run means, two-sided.

| comparison | registered grades | full-evidence pass |
|---|---|---|
| **F beats A** (primary) | +0.58, 49–23–24, **p = 0.036** | +1.03, 68–8–20, p = 0.0008 |
| **Q beats A** (primary) | +1.12, 65–25–6, **p = 0.012** | +1.16, 61–22–13, p = 0.0045 |
| F against Q | −0.54, 34–54–8, p = 0.17 | −0.13, 32–46–18, p = 0.70 |

Task 4 apart from the others, as the design requires:

| | F vs A | Q vs A | F vs Q |
|---|---|---|---|
| tasks 1 to 3, registered | +0.70, p = 0.042 | +0.55, p = 0.23 | +0.14, p = 0.71 |
| tasks 1 to 3, full evidence | +0.99, p = 0.006 | +0.62, p = 0.14 | +0.36, p = 0.31 |
| task 4, registered | +0.25, p = 0.74 | +2.83, p = 0.029 | −2.58, p = 0.029 |
| task 4, full evidence | +1.15, p = 0.086 | +2.77, p = 0.029 | −1.62, p = 0.029 |

With four builds against four, 0.029 is the smallest p one task can give. Grader agreement, r: 0.64, 0.89, 0.59, 0.92 (registered); 0.65, 0.75, 0.75, 0.93 (full evidence).

## What the graders opened (amendment 1)

The first graders of task 4 came back in 20 to 36 seconds, so their transcripts were checked. `grader_audit.py` counts the files each grader opened and never reads what it wrote.

| | pictures opened | sources read |
|---|---|---|
| registered quality graders (24) | 347 of 432: every desktop picture, 127 of 144 strips of the page in use, 76 of 144 phone pictures | 0 of 144 (9 partly printed by a shell command) |
| registered spread graders (12) | 189 of 288, at least one of every design | 0 of 144 (36 printed by a shell command) |
| full-evidence quality graders (24) | 432 of 432 | 144 of 144 |

The same count over the earlier tests shows this is how Sonnet 5.5 at medium effort grades with this prompt: Haiku graders opened 98 to 100% of the pictures and 83 to 100% of the sources, and Sonnet graders, in every test since test 15, opened 60 to 92% of the pictures and 0 to 28% of the sources. Tests 15 to 23 rest on grading of this kind.

The second pass used the registered prompt with three numbered steps in front of the scoring (open all 18 pictures, read all six sources, then score). All 24 graders did both on the first attempt. That is the plugin's own finding from test 23 again: a step that is mentioned is skipped, and a step that is numbered is done.

The two passes agree on most builds (r = 0.88 over the 48 run means). Reading everything left A where it was (+0.06) and Q nearly so (+0.10), and raised F by half a point (+0.51), almost all of it on the bento (+1.08) and the block world (+0.78). The graders' notes say why. From the pictures at rest, the bento F builds were marked down for a closed state that "shows no bento at all" and a popover that covers the headline. Graders who read the source and every strip wrote about what the component does: tiles that reflow between a row and a grid, focus handling, closing on Escape and on a click outside, tiles that work as real navigation. Whether a grader who reads the source is rewarding real behaviour or careful-looking code is not something this test can separate.

## Task by task

**1. Pelican.** The full build won (8.17 against 7.17 and 7.25). Its four sessions were dealt four kinds (seated on the saddle, bird on the bars, slim racer, cargo bike) and built four different bikes. A and Q built one picture four times each: a side view of a pelican on a red or teal bike, hills, a scrolling road. Every quick dump named that kind first, as the page tells it to, and it scored the same as the prompt alone.

**2. ASCII colour mixing.** Quick mode won (7.92), the full build was second (7.08), the prompt alone last (5.67). The prompt alone made four paint-on-a-grid canvases. The full build made four two-colour mixers with one ratio slider: its dump's thesis is about mixing two colours at a ratio, and all four dealt angles are forms of that. Quick mode's four dumps named four different engines (pots and a grid, a drop mixer, a paint grid, a blend field) and built them.

**3. Bento menu.** The one task where the registered grades put the prompt alone first. Quick mode lost on both passes (6.82 and 7.25 against 7.50 and 7.46). Its builds are close to the prompt-alone builds (a cream page, a dark pill, a panel that drops down; "Ember & Oak" on three of four, as on all four A builds) and two of them scored 5.67. The full build's four are four brands and four ways of collapsing, and they are what the two grading passes disagree about.

**4. Block world.** Quick mode won by nearly three points (8.75 against 5.92), 24–0–0. The full build barely moved (6.17). Its dump read the task as a grid editor: the five angles are flat block grid, toy box with a palette, stacked columns, paint-by-cell stroke and ghost-preview grid, all one kind seen five ways, and every F build opened on an empty flat grid with three or four kinds of block. The quick dumps listed side view, top-down and isometric as kinds, and their builds open on terrain or a built scene with nine or ten kinds of block. The angle rule (kinds of the thing, the one a stranger pictures first) is the rule the swarm's dump missed here.

## Criteria

Mean over the four tasks.

| | fidelity | correctness | craft | usability | overall |
|---|---|---|---|---|---|
| A, registered | 7.46 | 7.06 | 6.46 | 6.73 | 6.56 |
| F, registered | 7.50 | 7.71 | 7.36 | 7.21 | 7.15 |
| Q, registered | 8.08 | 7.61 | 7.67 | 7.42 | 7.69 |
| A, full evidence | 7.31 | 7.21 | 6.46 | 6.73 | 6.62 |
| F, full evidence | 7.81 | 8.08 | 7.67 | 7.73 | 7.65 |
| Q, full evidence | 8.34 | 7.94 | 7.75 | 7.69 | 7.79 |

Both dump arms gain most on craft. The full build's fidelity is level with the prompt alone on the registered grades.

## Spread and adherence

A variety score is not higher-is-better, so the graders were told what each task fixes and leaves open, scored spread only in what is open, and counted the builds that break what is fixed.

| task | spread in what is open, A / F / Q | builds of 4 that break what is fixed, A / F / Q |
|---|---|---|
| pelican | 2.33 / 4.67 / 2.00 | 0 / 0 / 0 |
| ASCII | 2.33 / 2.67 / 7.00 | 0 / 0 / 0 |
| bento | 2.00 / 8.00 / 3.33 | 0 / 0 / 0 |
| blocks | 2.33 / 2.67 / 5.33 | 0 / 0 / 0 |

No grader counted a break in any set. The prompt alone made one design four times on every task. Each dump arm was spread on two tasks and narrow on two, and never the same two: the full build is spread where its angles were different kinds (pelican, bento) and narrow where they were neighbours (ASCII, blocks); quick mode is the reverse. These graders opened one picture of each design and no source, so the break counts are weak evidence. The scripted checks below measure the mechanical part of what is fixed directly.

## Scripted checks

Written before any build, run on every build of every arm. Each arm passed 59 of 60.

| task | checks | A | F | Q |
|---|---|---|---|---|
| pelican | the main drawing is an SVG; no raster; it changes in the first 2 s; it still changes at 20 s | 16/16 | 16/16 | 16/16 |
| ASCII | a control changes the picture; ASCII text is on the page; no script errors | 12/12 | 11/12 | 12/12 |
| bento | it collapses; from the keyboard; a CSS grid of four or more; no real brand named | 16/16 | 16/16 | 16/16 |
| blocks | a control changes the picture; no script errors; 32 stands in the source as a size; no existing game named | 15/16 | 16/16 | 15/16 |

The three failures are the same check, `responds`, and all three are the capture's doing. It uses a page's first three controls in page order. On ASCII F-r1 it typed text that is not a colour into hex fields, which the page rightly refused. On blocks A-r2 and Q-r3 the first three controls are palette buttons, which change a few pixels of highlight. `handcheck.py`, written afterwards, clicks three cells of the world on all twelve block builds, and all twelve change. The failures are reported as recorded.

Two quick dumps for the block world describe a kind they did not build by an existing game's name. No page or source names one.

## Cost

Per build, as the harness reported it for each session:

| | A | F | Q |
|---|---|---|---|
| tokens | 80.7K | 117.8K | 91.8K |
| seconds | 44 | 109 | 148 |

Quick mode costs 14% more tokens than the prompt alone and takes more than three times as long, most of it looking and fixing. The full build's builder costs 46% more tokens, and it needs a dump first: the four dump builds took 19.9, 19.3, 40.2 and 21.4 minutes with 18, 20, 23 and 17 agents. Their main loops reported 195 to 212 thousand tokens; worker tokens were not measured here (test 23 measured about 2.6 million on one dump).

## What the builders did

Read from their transcripts (`process.json`).

| | F (16) | Q (16) |
|---|---|---|
| dealt a hand | 16 | not dealt; a quick dump is read whole |
| wrote the dump before the page | | 16 |
| looked | 16 | 16 |
| ran a scripted play | 4 | 13 |
| opened a picture the look saved | 13 | 15 |
| edited after the first look | 7 | 10 |
| refused a tool | 0 | 0 |

- **Two of the 16 full-build sessions dealt with `--no-ledger`** (bento F-r1, blocks F-r2), and each landed on an angle another session already had: two tin stacks, two toy boxes. The harness prompt says "Write only that file", and the ledger is a second file.
- **Nobody used the 20-second "let it run" wait.** The longest wait in any play was 6 seconds. On the pelican, the one task that is an animation, three of four quick builders and one full-build builder waited 3 to 6 seconds and looked again. The pelican's `still_animating` check passed on all twelve builds, so there was nothing for a longer wait to catch.
- **The quick dumps are 1.0 to 1.9 thousand tokens,** all 16 under the 2 to 4 thousand the page asks for. Each lists 3 or 4 kinds, 4 to 7 checks and 4 to 7 anti-keywords.
- **The full dumps are 27.5, 27.6, 44.0 and 31.4 thousand tokens** against a `lite` target of 8 to 15 thousand, with 63 to 127 entries and 21 to 35% of them collected. The bento dump ran one widening round and kept six `oversized_entry` warnings. They were used as create mode left them.

## Reruns, exclusions and departures from the design

- **Two dump builds were rerun once, from the start** (pelican, bento). The session allows 20 subagents at a time, and launching the twelve quick builders beside three running dump builds stopped two main loops before they had a dump. Their partial work is kept beside the test in `<task>/interrupted/` (work dirs hold pages from other sites and are not committed). The design allows one rerun for a dump build that ends without a dump.
- **No build was rerun. No grader was rerun.** Nothing is excluded.
- **Task 4's wording.** The owner's fourth task named an existing game and asked for a clone of it. The assistant running the test does not build recreations of a specific existing game, held the task, and offered three choices. The owner chose the genre wording, which was the assistant's suggestion. Task 4 is reported with the others and apart.
- **Amendment 1** (the grader audit and the second pass) was written before any score was read. The 36 registered judgment files were hashed unread at that point (`judgments-registered.sha256`) and still match.
- **Added after the builds:** `handcheck.py` (the block-world click check, post hoc), `grader_audit.py`, `full_pass.py`, the `grade_full` prompt, and an argument on `aggregate.py` and `pooled.py` to run the same analysis on the second pass.

## What would count against the final version

From `design.md`, with what happened.

1. **Either primary comparison failing to reach p < 0.025, or going the wrong way. One did.** F against A: p = 0.036. Q against A: p = 0.012.
2. **Q or F breaking what a task fixes more often than A. No.** No breaks counted in any set; 59 of 60 scripted checks for every arm.
3. **Q builders not writing the dump first, or fewer than three in four looking. No.** 16 of 16 and 16 of 16.
4. **(Amendment 1) A confirmed comparison failing on the full-evidence grades. No.** Q against A holds on both passes.

## What this does and does not show

- **Writing out what you know before the task helps on tasks the designer did not choose.** Quick mode's gain here (+1.12) is close to test 23's (+1.29), for 14% more tokens. It is not even across tasks: large on two, nothing on one, negative on one, and without task 4 it is not significant.
- **The full build's gain on outside tasks is about a third of what it was on the designer's tasks** (+0.58 here against about +2.1 in test 22). That gap is what a confirmation test exists to find. The stronger second reading is real data and was not the registered analysis.
- **This test gives no evidence that the swarm's dump beats the one-pass dump.** Test 23 had the swarm ahead by 0.54 (p = 0.28). Here quick mode is ahead by 0.54 on the registered grades (p = 0.17) and by 0.13 on the second pass (p = 0.70). Each won two tasks. The default was set on test 23's direction; that is the owner's call to revisit or keep.
- **Each arm narrows in its own way.** Quick mode builds the classic kind every time, so four sessions make the same thing when the classic is obvious (pelican, bento). The full build deals different angles, so it spreads when the dump's angles are different kinds, and it is held to the dump's reading of the task when they are not (the block world as a grid editor).
- **Grading by Sonnet at medium effort needs numbered steps and an audit.** Without them one task's order changed.

## Limits

- Graders are models from the same family as the builders. No human graded anything.
- Four builds per arm per task, and one dump per task for the full build: the block-world result is one dump's reading of one task.
- Four tasks, all small self-contained web pages.
- One builder model. `lite` depth only; the plugin's default depth, `standard`, has still never been A/B tested.
- The capture and the prompts were written by the designer, before the tasks were known. The capture shows only a page's first three controls, which is why a bento that opens from one handle shows one frame of use.

## Candidates for after the freeze

None of these is done. Each would need its own test before it changes the skill.

1. **A check that a dump's angles are different kinds.** The block-world dump passed every existing check with five angles of one kind.
2. **The ledger under a "write only this file" instruction.** Either the deal says the ledger is its own bookkeeping, or the harness stops saying it.
3. **The quick dump's size.** The page asks for 2 to 4 thousand tokens and builders write 1 to 2. Nothing here says which is right.
4. **The `lite` dump's size,** two to three times its target again.
5. **"Let it run".** Still validated only on past builds.
6. **Future tests:** the `grade_full` steps and `grader_audit.py` by default, and a capture that follows a control that opens more controls.
