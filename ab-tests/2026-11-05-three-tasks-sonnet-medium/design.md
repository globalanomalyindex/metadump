# A/B test 15: a hand, not the deck (metadump 0.10.0), same three tasks, Sonnet 5.5 at medium effort (2026-11-05)

Pre-registered before any run. Test 15 tests ADR 0015: the deal now gives each session a hand. A hand holds the user's words, every tier-1 entry, the worn paths and the review questions, plus a random half of everything else. Before, every session read the whole dump in a new order.

**Setup:**
- **Builders and graders:** Sonnet 5.5 at medium effort (the owner asked for Sonnet this time). Both arms are built fresh, because test 13's prompt-only builds were Haiku.
- **Dumps:** test 13's three dumps, built by the Haiku swarm (ADR 0008). They're re-finished with 0.10.0's `finalize.py`, which changes only the manifest (a `deal` note first, and `how_to_read` starting with the deal) and the routing line numbers.
- **Arms:** A = the task alone. B = the task plus the dump, read the way the 0.10.0 working tree's use mode describes (it starts with the deal). Prompts: the same as test 13 for both arms.
- **Runs:** 4 per arm per task, 24 builds.
- **Grading:** the same blind blocks, label orders and rubrics as tests 13 and 14: 6 graders per task plus 3 variety graders per task (P = A, B, A).

**Measures:**
- quality per task and pooled;
- variety;
- copying (`copying.py`);
- whether each B builder dealt, and the hand it got (from its transcript);
- for the haiku: 5-7-5 and cloud types;
- for the button: curve sets.

**Hypotheses:**
1. At least 10 of 12 B builders deal (test 14: 5 of 12).
2. B's variety ≥ A's on at least 2 of 3 tasks (tests 13 and 14: at most 1 of 3).
3. B ≥ A overall on at least 2 of 3 tasks: partial hands keep the quality.
4. No two B buttons share the same literal curve set, and the B haiku reach at least 3 cloud types.
5. On the toast, the dump's strongest task in tests 12 to 14, B ≥ A.

Any other result is reported as is.

**Confounds:**
- n = 4 per arm;
- one dump per task, made by Haiku while the builders are Sonnet;
- LLM graders;
- the model change means test 15 can't be compared number for number with tests 13 and 14, only arm against arm within itself.
