# A/B test 5: the shopping test from scratch on metadump 0.5.0 (2026-11-04)

Pre-registered before any run. Test 3 (`../2026-11-04-shop-haiku/`, 0.3.0) lost: A 7.04 vs B 6.33, win rate 0.29, because the dump narrowed the task to bare product cards. Test 4 (0.4.0) was stopped before results. 0.5.0 (commit 5b2efd1; ADRs 0005 and 0006) adds to 0.4.0's changes (seed, don't narrow; tier 1 collected-only; readings; research facets; screenshots; every image viewed) by identifying the task first: the disciplines it belongs to, a ladder from abstract to specific with a discipline primer at the top, and distilling references instead of copying them.

**Same as test 3:** the task ("make a compact, minimal, modern shopping component."), the delivery spec, Haiku 5.5 for everything at default effort, 4 runs per arm, two blind blocks of 4 with 3 graders each and the same label orders, the same rubric (compact, minimal, modern, usability, craft, overall), the same click test, and 1280x800 desktop shots with true 390x844 phone shots (`mobile.mjs`).

**From scratch:** both arms are rebuilt (A is not reused). B's dump is built by a Haiku main loop running create mode from the installed 0.5.0 (lite, no references), and B's builders follow 0.5.0's use mode.

**Primary outcome:** mean overall per arm and the B-vs-A win rate. **Secondary:**
- per-criterion means, especially usability and compact, where 0.3.0's B lost most;
- functional checks and cost;
- the dump's grounding line and warnings, whether it has a task ladder and a primer, whether a widening round ran;
- whether the B builds keep a complete shopping flow (cart, quantity, checkout).

**Hypothesis:** B ≥ A overall, with B recovering usability and compact and keeping its lead on minimal and craft. Any other result is reported as is.

**Known confounds:** n = 4; one task; LLM graders; the dump depends on one lite build; the repo's CLAUDE.md is visible to all builders.
