# A/B test 6: the shopping test from scratch on metadump 0.5.1 (2026-11-04)

Pre-registered before any run. Test 5 (`../2026-11-04-shop-haiku-v5/`, 0.5.0) flipped test 3's result: B 7.17 vs A 5.58, win rate 0.83, grader r 0.67. But B trailed on usability (6.75 vs 7.58): its builds had no bag review or checkout. 0.5.1 (commit 04d6c1a) targets that:
- dumps record the user's whole job end to end (`essence.task.job`);
- the default reading covers the whole job, verify walks it step by step, and use mode checks builds against it;
- the moodboard skips logos and blank images;
- verify runs again after a small widening.

**Same as test 5:** the task ("make a compact, minimal, modern shopping component."), the delivery spec, Haiku 5.5 for everything at default effort, 4 runs per arm, both arms built from scratch, two blind blocks of 4 with 3 graders each and the same label orders, the same rubric (compact, minimal, modern, usability, craft, overall), the same click test, and 1280x800 desktop shots with true 390x844 phone shots. The B dump is built by a Haiku main loop running create mode from the installed 0.5.1 (lite, no references), and B's builders follow 0.5.1's use mode (same builder prompt as tests 3 and 5, with the plugin path updated).

**Primary outcome:** mean overall per arm and the B-vs-A win rate. **Secondary:**
- B's usability against A's;
- how many B builds cover the whole job (a way to review the bag and to check out);
- the dump's grounding line, warnings, `essence.task.job`, the default reading, and whether verify re-ran after widening;
- moodboard noise;
- cost.

**Hypothesis:** B ≥ A overall again, and B's usability rises to at least A's, with B builds covering the whole shopping job. Any other result is reported as is.

**Known confounds:** n = 4; one task; LLM graders; one lite dump build; a fresh A arm whose quality varies run to run (test 5's A had a CSS bug in one run).
