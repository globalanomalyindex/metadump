# A/B test 8: three "sticky and punchy" bezier curves as loops, on metadump 0.7.0 (facets), Haiku everything (2026-11-05)

Pre-registered before any run. 0.7.0 (ADR 0009) writes every dump entry as a facet, the shape of the owner's hand-made dumps: a line of text, lists of short phrases, behaviors and a principle. The dump opens with a thesis, a summary and a formula with roles. The swarm, its verify and widening passes, tiers, provenance and `instead` rewrites stay as in 0.6.0. This is the first test of a motion task, and the first on the facet shape.

**Task (verbatim):** a set of three custom bezier curves that are described as feeling "sticky and punchy", present them as loops

**Delivery spec (both arms):**
- one self-contained HTML file that presents the three curves as looping animations;
- inline CSS and JS only, with no external requests, working from disk;
- the curves exposed for the harness as `window.CURVES = [{name, bezier: [x1, y1, x2, y2], duration_ms}]`: three items, the values the animations actually use. Graders can't feel easing from a still image, so the harness renders the exposed values the same way for every build.

**Arms:**
- **A:** task only.
- **B:** task plus a lite dump built by a Haiku main loop running 0.7.0 create mode from the working tree (uncommitted, on top of 02d3221). It uses plain Haiku subagents, no Workflow tool, and no references. B's builders follow 0.7.0 use mode, with the same prompt as tests 6 and 7 and the paths updated.

**Same as test 6:**
- Haiku 5.5 for everything at default effort;
- 4 runs per arm, both built from scratch;
- two blind blocks of 4, 3 graders each, with the same label orders;
- 1280x800 desktop shots and true 390x844 phone shots.

**What graders get for each label:**
- the desktop and phone screenshots;
- a frame strip (8 frames, 150 ms apart, of the running page);
- a standard curve sheet rendered by the harness from `window.CURVES`. Each curve gets its graph, a 24-step position strip (dense dots mean slow, sparse mean fast) and measured numbers: overshoot, time to 90%, start and end speed, and where peak speed falls;
- the source.

**Rubric (0–10):**
- **sticky:** the motion reads as sticky. It clings, lingers or grips somewhere in the move and lets go with intent.
- **punchy:** a fast, decisive attack or release with impact, not mushy.
- **distinct:** three clearly different curves that still work as a set.
- **presentation:** the loops show each curve clearly. Labeled, values visible and copyable, timing readable, seamless loops, works on a phone.
- **craft:** polish, hierarchy, type, spacing, code quality, reduced-motion handling.
- **overall.**

**Click test (headless Chrome):**
- `window.CURVES` holds 3 valid beziers;
- animations run (frames differ over time);
- the running animations use the declared curves;
- no JS errors;
- no overflow at 390 px.

**Primary outcome:** mean overall per arm and the B-vs-A win rate.

**Secondary outcomes:**
- per-criterion means, especially sticky and punchy;
- how the dump defines "sticky" and "punchy" (senses and readings), and whether B's curves follow it;
- the dump's size, entries, tokens, grounding line and warnings (including `wordy_entry`), and whether it has a thesis, summary and formula;
- the dump build's time and cost.

**Hypothesis:** B ≥ A overall. B's curves are more distinct and more deliberately sticky and punchy, because the dump pins down what the two words mean in motion terms. The dump comes out far smaller than 0.6.0 dumps (lite target 8–15K tokens). Any other result is reported as is.

**Known confounds:**
- n = 4 per arm, and one task;
- LLM graders judging motion from stills plus measured curves;
- one lite dump build;
- the `window.CURVES` requirement shapes both arms equally;
- "sticky" has several fair readings (a slow start, a magnetic settle, an overshoot that snaps back), so graders may disagree.
