# A/B test 18: 0.11.0 plus the look (metadump 0.12.0), Sonnet 5.5 at medium (2026-11-05)

Pre-registered before any run. Test 18 tests ADR 0018: use mode now ends with `look.py`, which renders the build headlessly, screenshots it at desktop and phone widths, hovers and opens it, and lists clipping, overlap, overflow and tiny targets for the builder to look at before finishing.

Why: in test 16 the 0.11.0 dump toasts lost 0–21–3 on craft (clipped timelines, overlapping icons, wrapped rows) and no builder had opened the page; in test 17 the 0.8.0 dump toasts lost on craft too. 0.11.0 had the best Sonnet button of any version (9–12–3) and was more varied on all three tasks, so the fix builds on it (ADR 0017, second decision).

**Setup:**
- **Plugin:** the 0.12.0 working tree: 0.11.0 plus `look.py`, a look step at the end of use mode, and a last reading step in every dump naming the look.
- **Dumps:** test 16's three dumps (built by 0.11.0's create mode on the Haiku swarm), re-finished with 0.12.0 so their `how_to_read` ends with the look. Nothing else in them changes.
- **A arm:** test 16's prompt-only Sonnet builds and timings, reused unchanged (they are also test 15's).
- **B arm:** 4 new builds per task on Sonnet 5.5 at medium, with the same dump-arm prompt as tests 13 to 16.
- **Grading:** fresh blind Sonnet graders, same blocks, label orders and rubrics; 6 per task plus 3 variety graders per task.

**Measures:** quality per task and pooled; variety; copying; whether each B builder dealt and whether it ran the look (from its transcript); for the toast, the craft score and the graders' layout complaints; for the button, dreamlike.

**Hypotheses:**
1. At least 9 of 12 B builders run the look (a printed command in the dump's reading steps; the deal reached 12 of 12 that way).
2. On the toast, B's craft ≥ 7.0 (test 16: 5.17) and the graders' notes stop naming clipping, overlap and wrapped rows.
3. B ≥ A overall on at least 2 of 3 tasks (test 16: 1 of 3).
4. B's variety ≥ A's on at least 2 of 3 tasks (test 16: 3 of 3).
5. Pooled, B wins more head-to-heads than it loses (test 16: 27–39–6).

Any other result is reported as is.

**Confounds:**
- n = 4 per arm; one dump per task, Haiku-built while the builders are Sonnet; LLM graders.
- A is reused from test 16, so its scores carry over; only B changes.
- The look adds a step that could also improve a prompt-only build; A doesn't get it, so a B gain is "dump plus look" against "prompt alone".
