# A/B test 9: rerun of test 8 after ADR 0010 (2026-11-05)

Pre-registered before any run. In test 8 (`../2026-11-05-curves-haiku/`), the dump defined "sticky" and "punchy" itself and proposed one "default set" of three curves. Every B build copied it, so B lost on distinctness (3.83 vs 6.67), tied on sticky and punchy, and won presentation and craft by a wide margin (8.17 vs 3.58, 7.25 vs 4.42). ADR 0010 changed 0.7.0 in four ways:
- quality words keep their readings side by side, with no default (`kind: "quality"` facets, `quality_one_reading`);
- the dump never produces the deliverable: pools hold exemplars per reading, and no default set exists;
- `open_questions` defaults settle parameters, never the work;
- verify gets a definition pass and a copy pass, and measures contradictions against collected tier-1 entries only.

It also dropped facet phrases from the index, added `oversized_entry`, and drops note-only sections. This rerun asks whether B keeps its presentation lead and gets distinct curves too.

**Same as test 8:**
- the task: a set of three custom bezier curves that are described as feeling "sticky and punchy", present them as loops;
- the delivery spec, including `window.CURVES`;
- Haiku 5.5 for everything at default effort;
- 4 runs per arm, both arms built from scratch;
- two blind blocks of 4, 3 graders each, with the same label orders;
- the rubric (sticky, punchy, distinct, presentation, craft, overall);
- the harness (`motion.mjs`: frames, curve sheet, animation checks), and the builder and grader prompts with paths updated;
- the dump-builder prompt. The one change is that it names verify's definition and copy passes along with the job and narrowing passes, since the main loop briefs verify itself.

The skill comes from the working tree: uncommitted 0.7.0 with ADR 0010, on top of 02d3221.

**Primary outcome:** mean overall per arm and the B-vs-A win rate.

**Secondary outcomes:**
- per-criterion means, especially distinct, presentation and craft;
- **curve diversity**, measured from `window.CURVES`:
  - within a build, the mean pairwise distance between its three curves' progress profiles (mean absolute difference over 101 time samples);
  - across an arm, how many distinct bezier tuples appear among its 12 curves. In test 8: B 4 distinct, A 10.
- the dump:
  - quality facets and how many readings each has;
  - whether any entry, export or default holds a finished set of three curves;
  - entries, tokens and index share;
  - warnings, including `quality_one_reading`, `oversized_entry` and `wordy_entry`;
  - what verify's definition and copy passes reported;
  - build time and cost.

**Hypothesis:**
- B's distinct score is clearly higher than in test 8 (at least 5.5) and close to A's;
- B keeps its presentation and craft lead;
- B ≥ A overall;
- B's 12 curves include at least 8 distinct tuples;
- the dump has a quality facet for each of "sticky" and "punchy" with at least two readings, and no finished set.

Any other result is reported as is.

**Known confounds:**
- n = 4 per arm, and one task;
- LLM graders judging motion from stills and measured curves;
- one lite dump build;
- a fresh A arm whose quality varies run to run (test 8's A had a build that rendered blank);
- graders differ from test 8's.
