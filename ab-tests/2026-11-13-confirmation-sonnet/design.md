# Confirmation test of the final version (pre-registered 2026-11-13, before any task was known)

Tests 1 to 23 were run by the person designing the plugin, on tasks that person chose. This test is the one that counts as confirmation: the skill is frozen first, the tasks come from outside the design afterwards, and everything below was written before either a task or a result existed.

## The frozen version

metadump 1.0.0 as it stood in the working tree at 2026-11-13T17:27Z. `frozen.sha256` lists the SHA-256 of all 33 files (everything under `skills/metadump/` plus `.claude-plugin/plugin.json`); the SHA-256 of that list is `58e5e12e7555770b6048c05f8f6f6fe5bf2674b380f9a64148e4869a98d29a24`. `shasum -a 256 -c frozen.sha256` from the repo root checks it. No file in that list changes until this test is written up. If one has to (a crash that stops the test), the change, the reason and the new hash go in an amendment here, and every build made before it is marked.

## Tasks

Two to four, received after the freeze, recorded verbatim below with the time received and where they came from. Either the owner names them, or they are drawn at random from a pool written by a model that is not told what the pool is for, with a seed taken from the operating system and recorded. The designer does not choose, reword or drop a task. A task that cannot be delivered as one self-contained HTML file or one markdown reply is replaced by the next from the same source, and the replacement is recorded.

Received from the owner on 2026-11-15, after the freeze (the hash list was checked again at 2026-11-15T20:50Z and matched), verbatim:

1. an SVG animation of a pelican riding a bike
2. a simple interactive ascii color mixing engine
3. a bento box-inspired collapsible UI menu component for a fictional coffee company site
4. a simple minecraft clone with a 32x32 block world

Tasks 1 to 3 run as written. Task 4 names an existing game and asks for a clone of it. The assistant running this test does not build recreations of a specific existing game, so task 4 was held and put back to the owner with three choices (a genre wording, a different task, or three tasks). The owner chose the genre wording, later on 2026-11-15, before anything was built for task 4:

4. a simple block-building sandbox game with a 32x32 block world

That wording was the assistant's suggestion, so task 4 is the one task whose words did not come from the owner alone. It is reported with the others and also apart from them.

### What each task fixes and leaves open, and its scripted checks

Written on 2026-11-15 before any build or dump of these tasks. The checks run on every build of every arm (`capture.py`). A check the script cannot decide for a page is recorded as not run, not as failed.

**1. Pelican.** Fixed: it is an SVG drawing that animates, and it shows a pelican riding a bicycle. Open: the style of drawing, the scene, how it moves, the colours, any controls.
- `svg_main`: the largest drawn element on the page is an `<svg>`, and no canvas or image is larger.
- `no_raster`: no `<canvas>`, `<img>` or SVG `<image>` anywhere.
- `animates`: the picture changes between 0 and 2 seconds, untouched.
- `still_animating`: it changes between 20 and 22 seconds too.

**2. ASCII colour mixing.** Fixed: it is a colour mixing engine (the person mixes colours and sees the result), drawn in ASCII characters, interactive, and simple. Open: which way of mixing it models, the controls, the layout, the characters it draws with, the colours on offer.
- `responds`: using at least one of its first three controls changes the picture.
- `ascii_text`: a `pre`, `code`, `samp` or `textarea`, or an element set in a monospace face, holds at least 40 visible characters that are not spaces. Not run when the main display is a canvas.
- `no_script_errors`: nothing is thrown on load or while its first three controls are used.

**3. Bento menu.** Fixed: it is a menu component for a coffee company's site, laid out like a bento box (a grid of compartments of different sizes), that collapses and expands; the company is fictional; it is a component, not a whole site. Open: the brand, its name and voice, colours and type, what the compartments hold, how the collapse behaves.
- `collapses`: there is a control with `aria-expanded`, or a `summary`, and using it changes the page.
- `keyboard`: that control can take keyboard focus, and Enter or Space toggles it.
- `grid`: some element laid out with CSS grid has at least four children.
- `fictional`: none of these names appears in the page: Starbucks, Dunkin, Costa, Nespresso, Nescafé, Peet's, Tim Hortons, Blue Bottle, Lavazza, Illy, Folgers, Maxwell House, Caribou, Dutch Bros, Intelligentsia, Stumptown, Philz, La Colombe, Tully's, Gloria Jean's, McCafé, Keurig.

## Arms

Four fresh builds per arm per task, Sonnet 5.5 at medium effort, each in its own session.

- **A:** the task alone.
- **Q:** the task plus quick mode (`references/quick.md`): the session writes its own dump in one pass, builds, checks and looks.
- **F:** the task plus a meta dump built for it by the frozen skill's create mode at `lite` depth (a Haiku 5.5 main loop at medium effort with Haiku workers, plain subagents), used the way the frozen SKILL.md's use mode describes. One dump per task, used as create mode leaves it.

Every test so far built its dumps at `lite`. The plugin's default depth, `standard`, has never been A/B tested, and this test does not test it either.

Prompts are the harness wording of tests 13 to 23, recorded in `prompts.py` before any build.

## What graders see, and the rubric

Decided now, so neither depends on the tasks.

- **A page:** desktop (1280×800) and phone (390×844) screenshots at rest; one strip of frames at 0, 2, 6 and 20 seconds untouched, then after each of the first three controls is used in page order; the source.
- **A written reply:** the markdown.

Each build is scored 0 to 10 on:

- **fidelity:** it is what the request asked for: all of it, nothing swapped for something else, and no more than any size word in the request allows.
- **correctness:** it works, or it is right: behaviour, facts, and the rules and standards of its form.
- **craft:** the quality of the making, visual, verbal or in code, whichever the task calls for.
- **usability:** clear and usable for the person it is for, including on a phone and from a keyboard where that applies.
- **overall:** holistic quality as a response to the task.

## Grading

Blind Sonnet 5.5 graders at medium effort, as tests 20 to 23: two blocks of six per task (runs 1 and 2 of each arm; runs 3 and 4), three graders per block, with the fixed label orders in `blind.py`. All graders are fresh. A grader that is cut off is rerun from the start and never resumed.

## Spread and adherence

A variety score is not higher-is-better (the owner, 2026-11-13). Before any build of a task, this file records what that task fixes and what it leaves open, in one line each. Three graders per task then score each arm's set for spread in what is open (0 to 10) and count how many of its four builds break what is fixed. Where a task has standards that a script can check (arithmetic, a verse form, contrast, keyboard reach), the checks are written here before any build and run on every build of every arm.

## Outcomes and analysis

**Primary:** overall score. For each pair of arms, head-to-heads within a grader's block pooled over tasks, and an exact stratified permutation test on run means (labels shuffled within task). Two primary comparisons, each two-sided at α = 0.025:

1. F beats A.
2. Q beats A.

**Secondary,** reported whatever they show: F against Q; each task alone; each criterion; spread and breaks; scripted adherence; tokens and time per build and per dump; what each builder did (dealt, wrote its dump first, looked, ran plays, let it run).

No result is dropped. No arm is rerun because it lost. No analysis is added that changes which arm looks better without being marked post hoc.

## Reruns and exclusions

Decided now. A build is rerun once, and only for these reasons: the session ended without writing its file; the session was refused a tool the skill tells it to use (the look, the deal); a usage limit cut it off. A dump build that ends without a dump is rerun once. Every rerun is listed with its reason. Nothing else is excluded.

## What would count against the final version

- Either primary comparison failing to reach p < 0.025, or going the wrong way.
- Q or F breaking what a task fixes more often than A does.
- Q builders not writing the dump first, or fewer than three in four of them looking.

Any of these is reported in the write-up's first paragraph.

## Limits known in advance

- Graders are models from the same family as the builders. No human grades.
- Four builds per arm per task; one dump per task for F.
- One builder model. Nothing here says how a stronger or weaker model behaves.
- The harness's capture and prompts were written by the designer, before the tasks were known.

**4. Block-building sandbox.** Written on 2026-11-15, after the owner's choice of wording and before any build or dump of this task. Fixed: it is a block-building sandbox game (a world made of blocks that the player can add to and take away from); the world is 32 by 32 blocks; it is simple; it is its own game and names no existing one. Open: two dimensions or three, the view, the kinds of block, the look, the controls, whether the player has a body.
- `responds`: using at least one of its first three controls changes the picture (a drag or click on the world counts).
- `no_script_errors`: nothing is thrown on load or while its first three controls are used.
- `world_32`: the number 32 stands in the source as a size.
- `own_game`: none of these names appears in the page or its source: Minecraft, Mojang, Creeper, Terraria, Roblox, LEGO.

## Amendment 1: what the graders opened (2026-11-15T21:50Z, written before any score was read)

**What was found.** The first graders of task 4 came back in 20 to 36 seconds, which is too fast to have opened everything the prompt tells them to open, so their transcripts were checked. `grader_audit.py` reads each grader's own transcript and counts the files it opened. For the 27 graders finished at that point (tasks 1, 2 and 4: 18 quality graders, 9 spread graders):

- Quality graders opened 249 of the 324 pictures they were shown (77%): every desktop picture, 91 of 108 strips of the page in use, and 50 of 108 phone pictures. On the pelican, where the strip is the only evidence of motion, they opened 25 of 36.
- They read none of the 108 sources with the Read tool. Nine were partly printed by a shell command; for the rest the grader counted bytes or matching lines.
- Spread graders opened 117 of 216 pictures (each opened at least one picture of every design) and no source with the Read tool.

The same count over the earlier tests in this repo shows it is how Sonnet 5.5 at medium effort grades with this prompt, and not new here: Haiku graders (the tests up to 2026-11-05) opened 98 to 100% of the pictures and 83 to 100% of the sources; Sonnet graders, in every test since, opened 60 to 92% of the pictures and 0 to 28% of the sources. Tests 19 to 23 rest on grading of this kind.

*Correction, added after the write-up:* the Sonnet-graded tests are tests 15 to 23, not 19 to 23.

**What was known when this was written.** No judgment file had been opened and nothing had been aggregated. The audit reads which files a grader opened, never what it wrote. `judgments-registered.sha256` holds the SHA-256 of each of the 27 judgment files as they stood; the bento files are added to it when they exist.

**What does not change.** The registered grading is the primary analysis, exactly as registered above: the same prompts, the same graders, nothing dropped and nothing rerun, and the bento graded the same way. The two primary comparisons are read from it.

**What is added.** A second pass, *full evidence*, over the same blind folders with the same rubric and the same label orders, by fresh Sonnet 5.5 graders at medium effort. Its prompt is the registered prompt with three numbered steps in front of the scoring (open all 18 pictures with the Read tool; read all six sources in full with the Read tool; only then score): `prompts.py grade_full`. A grade is accepted only when the audit of that grader's transcript shows all 18 pictures opened and all six sources read. One that falls short is moved aside unread and the grader is rerun fresh, up to three attempts in all; if none is complete, the attempt that opened the most is kept and marked. Grades go to `<task>/judgments-full/`, and the same analysis is run on them (`aggregate.py judgments-full`, `pooled.py judgments-full`).

**How the two passes are read,** decided now:

- A primary comparison counts as confirmed only on the registered grades, as registered.
- If a primary comparison reaches p < 0.025 on the registered grades and, on the full-evidence grades, fails to or points the other way, that goes in the write-up's first paragraph and the claim is limited to what both passes support.
- A difference that only the full-evidence pass shows is reported as found after the fact, not as confirmed.
- Both sets of numbers are printed side by side, whatever they show.

**Not regraded.** The spread graders. Spread and breaks are secondary outcomes, each grader saw every design at least once, and the scripted checks measure the mechanical part of what each task fixes directly. Their audit is reported as a limit.

## Post hoc notes (not part of the registered analysis)

- **Block world, `responds`.** The scripted check uses a page's first three controls in page order. On two builds (A-r2, Q-r3) those are three palette buttons, which change a few pixels of highlight and stay under the check's 0.3% threshold, so the check records a failure. `handcheck.py`, written after that capture, clicks three cells of the world itself on all twelve builds; all twelve change. The check's result is reported as recorded, with this beside it.
- **ASCII, `responds`.** F-r1 fails for a like reason: the capture typed text that is not a colour into its hex fields, which the page rightly refused.

## Written up

2026-11-15: `writeup.md`. The 24 full-evidence grades were all accepted on the first attempt (`full-pass.json`). The freeze ends here; `frozen.sha256` still matched when the write-up was finished.
