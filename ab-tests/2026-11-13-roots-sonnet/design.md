# A/B test 23: the one-page roots skill against 0.13.0 and the prompt alone (2026-11-13)

Pre-registered before any roots build ran.

The plugin began as one request to a model before a task: write a structured JSON file of what you know (keywords in tiers, descriptions, tokens, anti-keywords), branching from the broad disciplines down to the specifics, with the steps, tricks and tests practitioners use. The idea behind it is that a model doesn't know what it knows until it writes it out. Twenty-two tests later, create mode is a swarm of about twenty Haiku workers with discovery, scraping, a moodboard, verify passes and a widening round. A dump takes about 25 minutes, and the main loop alone reports 200 thousand tokens.

No test has compared that swarm with the original idea done by the model that does the task. Test 7 tried a one-agent build with Haiku writing for Haiku, and it was weaker; that was before the look and before the lessons below. Test 22 showed that most of 0.13.0's gain over 0.12.0 comes from how the dump is used, since both arms read the same dump.

**The roots skill** (`skill-roots/SKILL.md`, one page): before the task the builder writes its own dump in one pass (three levels: disciplines, the thing itself, this task's specifics; keywords in tiers, descriptions, steps, tricks, tests, tokens as ranges, anti-keywords with what to do instead), then does the task with it, asks its own checks of the result, and runs the look. It keeps four lessons as one line each: the user's words are never narrowed and a size word bounds the build; cover the whole job; kinds of the thing with the classic first; a resource, not a rulebook. No workers, no research, no verify, no deal, no finalize.

**Tasks.** Test 22's two: "a lava lamp" and "a basic calculator".

**Arms.**
- **A** (prompt alone) and **C** (0.13.0: the swarm's dump, dealt, looked at): test 22's own builds, copied unchanged.
- **R:** 4 fresh builds per task, Sonnet 5.5 at medium effort, given the task and the roots skill. Each session writes its own dump and builds from it.

**Grading.** As test 22: blind Sonnet 5.5 graders at medium effort, two blocks of six per task (runs 1–2 and 3–4 of A, C and R), three graders per block, the same label orders; three variety graders per task. All grading is fresh, so A and C are scored again beside R. Same rubrics, capture script and scripted checks.

**Hypotheses.**
1. R beats A pooled (more wins than losses) and on each task.
2. R is within half a point of C on each task. The stronger form: R does not lose to C pooled (wins ≥ losses).
3. R costs less: its builder uses no more tokens and time than C's builder, and there is no dump build.
4. On the calculator, R's `basic` is 7.5 or more, and R's builds pass as many scripted checks as A's and C's.
5. R's sets are less varied than C's. Four separate sessions each write their own dump and each builds the classic kind, so this is expected; it is measured to know the price.
6. All 8 R builders write the dump before the HTML, in one write, and at least 6 run the look.

**What the result decides.** If R is within half a point of C on both tasks, the one-page skill becomes the proposal for the plugin's default, with the swarm kept only as an optional deep mode or dropped. If R is more than a point below C on either task, the report says what the swarm's dump added there, and the proposal is a middle path.

**Confounds.**
- A and C are the same sixteen files as in test 22; only R is new. n = 4 per arm per task, LLM graders.
- The roots skill was written after test 22's results on these two tasks were known. It names neither task and carries only the general lessons, but it was not written blind to them. A task chosen afterwards would be cleaner.
- R's dump and build come from the same Sonnet session. C's dump was built by Haiku workers and read by Sonnet. So R against C compares two whole pipelines, not only one pass against many.
- R reads a one-page skill; C reads SKILL.md and use.md, which are several times longer.

## Amendment, made before any roots build was captured or graded

The first eight roots builds are set aside in `r0/`, ungraded. Only three of the eight builders looked at what they built (three lava lamp builders, no calculator builder), for two reasons that are the harness's and the page's, not the idea's:

- The first version of the skill pointed at `look.py` in the main skill's folder, while the build prompt said to read no other files in the repo. Two builders tried to run it and the session's permission check refused.
- The skill mentioned the look in a paragraph under "Do the task with it", and three builders did not try it. Every 0.13.0 builder looked, and 0.13.0 gives the look its own numbered step.

So the look's scripts now sit inside the roots skill's own folder (`skill-roots/scripts/`, copies of the working tree's), the look is its own numbered step, and the build prompt says the scripts folder is part of the skill. Nothing else in the skill changed. The eight builds were rerun from the corrected skill and are the R arm. `r0/` is kept as it is: a set of roots builds that mostly went unlooked at.

## Second amendment, made before any grading

The owner pointed out (2026-11-13) that a variety score is not higher-is-better: where a task has rules or standards, builds agreeing on them is a benefit, and tests 12 to 22 counted any difference as variety, including one that breaks what the thing is. So the variety graders here are told what each task fixes and what it leaves open, score variety only in what is open, and separately count how many of a set's four builds break what is fixed (`prompts.py`). Hypothesis 5 is read against the new variety score. Quality grading is unchanged.
