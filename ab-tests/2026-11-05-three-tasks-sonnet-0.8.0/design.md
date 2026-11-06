# A/B test 17: metadump 0.8.0, the best-scoring version, retested on Sonnet 5.5 at medium (2026-11-05)

Pre-registered before any run. 0.8.0 (ADR 0012) scored best of all versions on these three tasks in test 12 (everything on Haiku 5.5 at medium): 7.50 vs 6.33, toast 24 of 24, pooled p = 0.045. The owner chose to go back to 0.8.0 (ADR 0017) and retest it with Sonnet 5.5 at medium. These are the numbers and examples for the public write-up.

**Setup:**
- **Plugin:** 0.8.0, restored exactly from the file-history snapshot taken right after test 12.
- **Dumps:** test 12's three dumps, built by 0.8.0's create mode (the Haiku swarm at medium effort), copied unchanged.
- **Builders:** Sonnet 5.5 at medium, 4 per arm per task, both arms fresh.
  - A gets the task alone.
  - B gets the task, the dump and test 12's exact dump-arm prompt ("consult it the way Use mode describes … It's a resource, not rules: the task and your judgment decide").
- **Graders:** Sonnet 5.5 at medium, blind, with the same blocks, label orders and rubrics as tests 12 to 16. That's 6 per task plus 3 variety graders per task (P = A, B, A).

**Measures:** quality per task and pooled, variety, copying, the haiku's 5-7-5 count and cloud types, and builder cost.

**Expectations (from test 12 and the Sonnet tests since):**
1. B ≥ A overall on at least 2 of 3 tasks.
2. B's variety ≥ A's on at least 2 of 3 tasks.
3. Pooled, B wins more head-to-heads than it loses.

Sonnet's prompt-only builds are much stronger than Haiku's (tests 15 and 16), so the margins may be smaller than test 12's. Any result is reported as is.

**Confounds:**
- n = 4 per arm;
- one dump per task, built by Haiku while the builders are Sonnet;
- LLM graders.
