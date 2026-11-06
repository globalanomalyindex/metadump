# A/B test 12: three tasks, Haiku 5.5 at medium effort for everything, metadump 0.8.0 (2026-11-05)

Pre-registered before any run. This is the first test of 0.8.0 (ADR 0012): the dump surfaces material to play with and gives no instructions.
- The head offers several contrasting angles instead of one recipe.
- The head, the exports and the review prompts are written as material, not orders (`directive_voice`, `no_angles`).
- Pools have no order; they mix deep cuts with the obvious items and give no item star billing.
- Use mode is a play loop: your own take, spread the material out, pick what sparks something, combine, turn the dials, sketch variations, and let chance pick when torn.
- Verify has a voice pass, which reports narrowings of kind `directive`.

Test 11 (0.7.1, Haiku at low effort) prompted the change: all four dump-built poems chose the same cloud, the one the dump's brief told them to choose and described first. Test 11 is not published, and its files stay in `../2026-11-05-four-tasks-haiku-low/` as the record.

The plugin runs from the working tree (`skills/metadump/` at 0.8.0, not yet released), so nothing is pushed for this test.

**Tasks (verbatim):**
1. `t1-button`: a button with custom bezier curve hover state animations that makes it feel dreamlike and ethereal, but practical for a website
2. `t2-haiku`: a haiku about rare clouds
3. `t3-toast`: a dark mode, very compact collapsible toast UI menu for tracking a package

**Delivery:**
- **HTML tasks (1 and 3):** one self-contained HTML file. Inline CSS and JS, no external requests, works from disk, interactions update state.
- **Haiku (2):** a markdown file holding exactly what the writer would reply to the user.

**Arms:**
- **A:** task only.
- **B:** task plus a lite dump of that task, consulted the way use mode describes. The B prompt is test 11's, pointing at the working-tree skill.

**Models:** every agent runs on Haiku 5.5 at **medium** effort.
- builders, both arms;
- the dump main loop, one per task, running 0.8.0 create mode with plain subagents and no Workflow tool, and every worker it spawns;
- graders.

**Per task:**
- 4 runs per arm, both arms from scratch.
- Two blind blocks of 4, 3 graders each, with the same label orders as earlier tests.

**What graders see:**
- **Button:** desktop and phone shots, a frame strip of hover in and out cropped around the button, and the source.
- **Toast:** desktop and phone shots at rest, a frame strip of the toggle opening and closing, the open state on desktop and phone, and the source.
- **Haiku:** the markdown.

**Rubrics (0–10, each ends with overall):**
- **button** (as in tests 10 and 11):
  - dreamlike;
  - practical;
  - motion;
  - craft.
- **haiku** (as in test 10):
  - imagery;
  - form: 5-7-5, or a deliberate short-long-short;
  - specificity: rare clouds, named or accurately evoked;
  - freshness;
  - resonance.
- **toast** (test 10's, plus dark mode):
  - compact;
  - collapsible;
  - tracking: status, timeline, ETA, carrier, number, next step;
  - dark: a real dark mode, with dark surfaces, readable contrast and accents that hold up on dark;
  - usability;
  - craft.

**Variety (new, the outcome this change targets):**
- **Variety graders:** per task, 3 Haiku-medium graders each see all 8 builds as two anonymous sets of four, P and Q. Which arm is P is fixed per grader: A, B, A. Each scores each set 0–10 for variety ("four different takes" vs "one idea four times") and says which set is more varied.
- **Haiku:** I count the distinct cloud types each arm's four haiku name or clearly describe.
- **Button:** I count how many builds in each arm share a cubic-bezier with another build in the same arm.

**Click tests (headless Chrome):**
- **Button:** hover changes the button, a custom `cubic-bezier` is used, `prefers-reduced-motion` is handled, JS errors, overflow at 390 px.
- **Toast:**
  - a toggle is found;
  - the state changes on click;
  - collapsed and expanded heights;
  - the surface is dark (the toast's background luminance);
  - JS errors, overflow at 390 px.
- **Haiku:** line count, and syllable counts (best effort).

**Featured runs:** run 1 of each arm per task, chosen now.

**Primary outcome, per task and pooled:**
- the mean overall per arm;
- the B-vs-A win rate;
- an exact permutation test per task, and a stratified one pooled.

**Secondary outcomes:**
- variety, as above;
- per-criterion means;
- the click tests;
- dump size;
- whether a widening round ran;
- warnings, including the new `directive_voice` and `no_angles`;
- whether the dump heads are written as material, with no rule words and with angles.

**Hypotheses:**
- B ≥ A overall on at least 2 of the 3 tasks.
- B's variety score ≥ A's on at least 2 of the 3 tasks. In test 11, B's poems converged on one cloud.
- B's four haiku name at least 3 distinct cloud types.

Any other result is reported as is.

**Known confounds:**
- n = 4 per arm per task.
- LLM graders, which judge motion from frames.
- Medium effort changes builders and dumps at once relative to test 11.
- One dump per task.
- The haiku and button tasks repeat earlier tests' subjects, but no earlier dump or build is reused.
- The variety graders know they are comparing sets, though not which arm made which.
