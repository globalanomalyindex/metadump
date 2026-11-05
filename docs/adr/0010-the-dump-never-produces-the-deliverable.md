# The dump never produces the deliverable, and quality words keep their readings

A/B test 8 (`ab-tests/2026-11-05-curves-haiku/`) asked for three bezier curves that feel "sticky and punchy", presented as loops. The 0.7.0 dump defined both words itself ("sticky: within 1 percent of rest by about 0.65 of the run"), ruled out the other readings with a `never_implies`, proposed a "default set" of three curves, named it in two `open_questions` defaults, led the "write the curves" route with it, and let verify tune the curves against the definition it had made up. All four builds that read the dump used that set. Their curves were near-identical (distinct 3.83 vs 6.67 for the prompt-only arm) and no more sticky or punchy than the prompt-only builds, while presentation and craft were far better (8.17 vs 3.58, 7.25 vs 4.42). The same thing happened in test 2 with a wrong hex value and in test 3 with a reading of "compact": a small model follows the concrete thing it is handed.

ADR 0005 kept scope readings side by side and said "decision points, not answers". It left two doors open: a quality word could still be defined once, and the dump could still propose the finished work as a default.

We decided:
- **Quality words get readings, with no default.** Each quality word in the prompt becomes a `kind: "quality"` facet whose `readings` list every plausible reading for the task, each with what it looks like in practice. finalize warns at fewer than two (`quality_one_reading`). Research covers an exemplar per reading.
- **The dump never produces the deliverable.** When the task asks for N things, no entry, export or default holds a finished set of N. Candidate pools hold one or two exemplars per reading, labeled by the reading each serves; the consumer composes the set.
- **A default settles a parameter, never the work.** `open_questions` defaults cover what the prompt left open and the work can't proceed without (currency, framework, a settle band), not the deliverable, a quality reading or a scope reading.
- **Verify checks for both.** Its contradiction pass measures values only against tier-1 collected entries, never against the build's own definitions. A definition pass reports a quality defined once or values fitted to a self-made definition; a copy pass reports any entry or group a consumer could paste as the whole job. Gap rounds widen such narrowings with readings and exemplars, never by retuning values.

Alongside, from the same test's dump: facet phrases (`properties`, `descriptors`, `signals`) are no longer indexed, since indexing them made the index as large as the body (25K of 53K tokens); a facet over about 300 tokens warns (`oversized_entry`); and a section left with only notes is dropped (`empty_section_dropped`).

We rejected:
- banning concrete values altogether, because measured and sourced values are what the dump is for; the problem is a proposed set presented as the answer;
- a per-task rule ("for creative tasks"), because the same copying happened on a shopping component and a hex value;
- detecting "a finished set of N" in finalize, because it would need to parse the prompt for counts; verify's copy pass does it with judgment.

## Consequences

- Dumps for "make me N things" tasks hold no ready-to-paste set. Consumers get readings, exemplars per reading, decision points and signals, and compose their own.
- Measured in A/B test 9 (`ab-tests/2026-11-05-curves-haiku-v2/`), a rerun of test 8: B 7.67 vs A 4.50, win rate 1.0, p = 0.029. Distinct went from 3.83 to 7.08 and presentation held at 8.5. None of B's 12 curves was copied from the dump, and all 12 were different (test 8: 4 distinct, 11 copied).
