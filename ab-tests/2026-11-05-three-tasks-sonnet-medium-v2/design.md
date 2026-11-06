# A/B test 16: amplify the user's words (metadump 0.11.0), dumps rebuilt, Sonnet 5.5 at medium (2026-11-05)

Pre-registered before any run. Test 16 tests ADR 0016. In test 15 the button dump called the usual dreamlike moves worn paths, with tamer replacements, and the dump buttons lost 1–21–2. 0.11.0 changes how dumps are built:
- the usual moves for the user's quality words are material to push further;
- a worn path's `instead` goes further, never back (`tamed_instead`);
- a constraint word says what has to keep working, not how much quality to give;
- verify reports taming (`tamed`);
- the deal deals the dump's own worn paths too.

**Setup:**
- **Dumps:** rebuilt from scratch with the 0.11.0 working tree, lite depth, the same way test 13's were built. The create-mode main loop and every worker run on Haiku 5.5 at medium effort, with plain subagents and no Workflow.
- **A arm:** test 15's prompt-only builds (Sonnet 5.5 at medium), reused unchanged with their timings.
- **B arm:** 4 new builds per task on Sonnet 5.5 at medium, with the same dump-arm prompt as tests 13 to 15.
- **Grading:** fresh blind graders on Sonnet 5.5 at medium, with the same blocks, label orders and rubrics, plus 3 variety graders per task.

**Measures:**
- quality, pooled and per task;
- variety;
- copying;
- the deal rate and each hand;
- `tamed_instead` and verify's `tamed` findings for each dump;
- the button's dreamlike score;
- the haiku's 5-7-5 count and cloud types.

**Hypotheses:**
1. No rebuilt dump marks the user's quality moves as not wanted: `tamed_instead` is 0 at the final check, and the button dump has no worn path for glow, glass, bloom, haze or float.
2. On the button, B's dreamlike score ≥ A's (test 15: 6.17 vs 8.25), and B ≥ A overall.
3. B ≥ A overall on at least 2 of 3 tasks.
4. B's variety ≥ A's on at least 2 of 3 tasks.
5. At least 10 of 12 B builders deal.

Any other result is reported as is.

**Confounds:**
- n = 4 per arm;
- one dump per task, built by Haiku;
- LLM graders;
- A is reused from test 15;
- a rebuilt dump differs in content as well as voice, so a change in B can't be pinned on one rule.
