# A/B test 4: the shopping test rerun on metadump 0.4.0 (2026-11-04)

Pre-registered before any run. Test 3 (`../2026-11-04-shop-haiku/`) found the 0.3.0 dump narrowed the task and lost: A 7.04 vs B 6.33 (v2 grading), win rate 0.29. 0.4.0 (commit fc435ff, ADR 0005) changes how dumps are built and used: tier 1 collected-only, readings kept side by side, research facets, associations, decision points, screenshots, every image viewed, grounding and narrowing checks, one lite widening round, and "your own take first" in use mode. This test asks whether that changes the result.

**Identical to test 3:** the task ("make a compact, minimal, modern shopping component."), the delivery spec, Haiku 5.5 for everything at default effort, 4 runs per arm, two blind blocks of 4 with 3 graders each and the same label orders, the same rubric (compact, minimal, modern, usability, craft, overall), the same click test, 1280x800 desktop shots and true 390x844 phone shots (`mobile.mjs`).

**Changed:**
- B's dump is built by a Haiku main loop running create mode from the installed 0.4.0 (lite, no references), and B's builders follow 0.4.0's use mode.
- **A is reused, not rebuilt.** A's four runs are test 3's (prompt only, so the plugin version cannot affect them). They are re-graded fresh alongside the new B runs, so no score carries over.

**Primary outcome:** mean overall per arm and the B-vs-A win rate. **Secondary:** per-criterion means (especially usability and compact, where 0.3.0's B lost most), functional checks, cost, the dump's grounding mix and whether finalize flagged narrowing, and whether the B builds keep a cart or quantity flow.

**Hypothesis:** B's gap to A closes (B ≥ A or within 0.3 overall), mainly by recovering usability and compact. A worse or unchanged result is reported as is.

**Known confounds:** n = 4; one task; LLM graders; reusing A means A's runs were made earlier in the day (same model, prompt and spec); the dump depends on one lite build.

**Stopped (2026-11-04):** the user switched to testing 0.5.0 before this run finished. The 0.4.0 dump build had reached verify, whose narrowing pass reported narrowings and contradictions, and was starting its widening round. No B runs or grades exist; see `../2026-11-04-shop-haiku-v5/` for the 0.5.0 test.
