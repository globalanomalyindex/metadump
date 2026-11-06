# A/B test 14: the deal (metadump 0.9.0), same three tasks, Haiku 5.5 at medium effort (2026-11-05)

Pre-registered before any run. Test 14 isolates one change: use mode's new first step, the deal (ADR 0014, `scripts/deal.py`).

Test 13 (`../2026-11-05-three-tasks-haiku-medium-v2/`, 0.8.1) fixed the haiku form and cut verbatim copying, but the dump builds converged on whatever the dump listed first: the first angle, the first spread values, the palette. The prompt-only side was rated more varied on all three tasks.

**What is reused, and what is new:**
- **Reused unchanged from test 13:**
  - the three dumps (copied into `*/metadumps/`);
  - the prompt-only builds A-r1 to A-r4 for each task, and their timings.
- **New:** four dump builds (B) per task, from the same dump-arm prompt as test 13. The only difference is the skill they read: the working tree at 0.9.0, whose use mode starts with the deal. Each B builder runs `deal.py` itself, so each gets its own random hand and dealt copy.

So any change in B against test 13's B comes from the deal and 0.9.0's use-mode text, not from the dumps or the A arm.

**Grading:** fresh blind graders on the same blocks, label orders and rubrics as test 13. That's 6 per task, plus 3 variety graders per task (P = A, B, A). Everything runs on Haiku 5.5 at medium effort.

**Measures:**
- quality per task and pooled (as before);
- variety graders' scores;
- copying (`copying.py`);
- for the haiku: exact 5-7-5 count and distinct cloud types;
- for the button: per-build curve sets;
- whether each B builder ran the deal: checked in its transcript, and the hand it got.

**Hypotheses:**
1. Every B builder runs the deal (4 of 4 per task).
2. B's variety ≥ A's on at least 2 of 3 tasks (test 13: 0 of 3).
3. B haiku reach at least 3 distinct cloud types and keep at least 3 of 4 at 5-7-5.
4. No two B buttons have identical curve sets (test 13: two identical pairs).
5. B ≥ A overall on at least 2 of 3 tasks.

Any other result is reported as is.

**Confounds:**
- n = 4 per arm;
- one dump per task;
- LLM graders;
- the A arm is reused, so test 14's A is test 13's A;
- the hand is random, so test 14's B shows one draw of four hands per task.
