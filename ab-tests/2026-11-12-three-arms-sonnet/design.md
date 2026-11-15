# A/B test 20: metadump 0.13.0 against 0.12.0 and against the prompt alone, on three new tasks (2026-11-12)

Pre-registered before any dump or build ran. Tests 18 and 19 compared a dump arm with the prompt alone. This one asks a different question: does 0.13.0 (deals that rotate, ADR 0019; a look that plays the page, ADR 0020) build better and more varied things than 0.12.0 from the same dump? It keeps the prompt-only arm so the result joins the earlier rounds.

**Tasks.** Three it has never seen, one per category, chosen by Claude before anything ran (the owner named no tasks this time). They mirror round 2's shapes: a creative text with a real genre behind it, a small "simple" interactive app, and a visual thing to recognise.

1. **imaginative:** "a field guide entry for a dragon"
2. **technical:** "a simple pomodoro timer"
3. **visual:** "a snow globe"

No 0.13.0 code was written against these tasks. Its checks were chosen from grader notes on tests 16 to 19 and tried only on those tests' builds.

**Arms.** 4 fresh builds per arm per task, Sonnet 5.5 at medium effort.
- **A:** the task alone.
- **B:** the task plus the dump, used the way 0.12.0's SKILL.md describes. The skill is the released 0.12.0 (`git archive 9d9a54e skills/metadump`, in `skill-prev/`): independent deals, a look that renders and hovers.
- **C:** the task plus the dump, used the way 0.13.0's SKILL.md describes (the working tree, frozen for the test): deals that rotate through a ledger, a look that plays the page.

**Dumps.** One per task, built fresh at lite depth by 0.13.0's create mode: a Haiku 5.5 main loop at medium effort and Haiku workers, plain subagents, no Workflow, as in test 19. No references. B and C read the same entries: the work dir is finalized twice, by 0.13.0 for C (`metadumps/`) and by 0.12.0 for B (`prev/metadumps/`), so only the reading notes in the manifest differ. Whatever 0.13.0's create mode adds (four to six angles that are different finished things, review questions written as plays) reaches both dump arms, so C against B measures the use-mode changes only.

**Prompts.** The same harness wording as tests 13 to 19. The field guide entry is a markdown reply. The timer and the snow globe are one self-contained HTML file each (inline CSS and JS, no external requests, working from disk). All three arms get identical delivery lines; B and C add the same dump paragraph, pointing at their own skill folder and dump file.

**Grading.** Blind Sonnet 5.5 graders at medium effort. Two blocks per task (runs 1 and 2 of each arm; runs 3 and 4), six builds per block, three graders per block with fixed label orders (`blind.py`). Three variety graders per task see the three sets of four as P, Q and R, with the arm behind each letter rotated per grader (`variety.py`).

**What graders see.**
- field guide: the markdown replies.
- timer: desktop and phone at rest; a strip of the timer started, running, paused and reset; the source.
- snow globe: desktop and phone at rest; a strip of frames untouched, then while dragging across it and after; the source.

**Rubrics (0 to 10 each).**
- field guide: imagination; fieldguide (it works as a field guide entry: identification, range and habitat, behaviour, similar species, status; compact and usable); specificity (concrete, consistent natural history, true to the lore it draws on); voice; freshness; overall (including its length).
- timer: simple (a simple pomodoro timer, complete and not overbuilt); correctness (counts down accurately, start, pause and reset work, moves between work and break, no drift or double timers); usability (time and mode clear at a glance, keyboard and screen reader, phone); craft; code; overall.
- snow globe: likeness (unmistakably a snow globe: a glass dome on a base, a scene inside, snow); visuals (glass, light, depth, the scene); motion (snow that falls and settles, a shake or other interaction that feels right); presentation (staging, polish, phone); overall.

**Measures.** Quality per task and pooled for each pair of arms (head-to-heads within a grader's block, and an exact stratified permutation test on run means); variety per set; the angle each dump session was dealt (from transcripts); whether each dump builder dealt, ran the look, how often, and whether it read the result; for C, which findings the look printed and whether the build changed after; what 0.13.0's look reports on every finished build of every arm (a check on the mechanism, not an outcome, since C's builders saw those findings); functional checks (timer: the time falls after start, holds when paused, returns on reset; globe: it moves untouched, and changes when dragged); the entry's length; tokens and time per build and per dump.

**Hypotheses.**
1. C ≥ B overall on at least 2 of 3 tasks, and pooled C wins more head-to-heads against B than it loses.
2. Pooled, C wins more head-to-heads against A than it loses, as B did in tests 18 and 19.
3. C's four sessions start from four different angles on every task with at least four angles, and C's variety ≥ B's on at least 2 of 3 tasks.
4. All 12 C builders deal, and at least 7 of the 8 HTML C builders run the look.
5. C's finished HTML builds carry fewer findings from the look's playing checks than B's.
6. On the timer, C's `simple` score is not below A's.
7. On the field guide, where the look does nothing, C and B differ in variety and not in quality.

Any other result is reported as is.

**Confounds.**
- n = 4 per arm per task; one dump per task, built by Haiku while the builders are Sonnet; LLM graders.
- The tasks were chosen by the same model that built 0.13.0, before any run, and not by the owner.
- Graders see six builds at a time here and four in earlier tests, so absolute scores don't carry across tests; arms are compared within this test only.
- A has no look. C against A is "dump plus deal plus look" against "prompt alone", as before; C against B is the comparison that isolates 0.13.0.
- The no-external-requests rule makes the snow globe hand-drawn in every arm.
