# The three dumps (0.8.0 create mode from the working tree, lite, Haiku 5.5 at medium effort for the main loop and every worker)

Taken from each dump agent's report, plus my own read of the head and the brief. Main-loop usage only.

## t3-toast: compact-toast-tracker.metadump.json
- 76 entries, ~27K tokens (108 KB). Grounding 24/76 collected (32%), 6 hosts.
- Thesis: "A parcel's state is a fact people glance at many times, so the most useful surface answers it before anyone opens it." It's an insight about the subject, not a recipe.
- Angles: the glance, the ledger, the quiet dark, the change.
- The LLM brief uses the new blocks (On the table, Ways in, Dials, Worn paths, Open), with no `Core:` and no rule words. Its readings give a default (persistent panel) and six alternatives. Quality facets for "very compact", "collapsible" and "dark mode" carry 4–5 readings each.
- Final check: 0 errors, 3 warnings (oversized_entry 2, quality_one_reading 1); no `directive_voice`, no `no_angles`.
- Discovery: 3 pages (one failed by content type), 26 images collected, 4 described and 22 skipped with reasons. No video.
- Verify ran twice per job. In round 1, the narrowings found included `directive` in both jobs. A widening round ran, and re-verify still listed some contradictions and narrowings (left open, at lite's cap).
- 21 agents. Main loop: 228,261 tokens, 1538 s (25.6 min).

## t2-haiku: rare-cloud-haiku.metadump.json
- 66 entries, ~26K tokens (105 KB). Grounding 23/66 collected (35%), 10 hosts.
- Thesis: "Rare clouds reach a haiku through what the eye can name and place, and the reading of rare that is chosen decides which seen thing carries it."
- 5 angles: the lens that stands still; the streak found by searching; colour after the sun; the thin edge; an autumn dusk. The quality facet "rare" has four readings and no default.
- Discovery: 1 video (a noctilucent timelapse on Commons), 3 pages (WMO nacreous, a 2008 nacreous gallery, APOD lenticular), 3 images. The moodboard holds 30 images, 6 described.
- Verify round 1: 0 contradictions. Narrowings included `directive` 5 times across the two jobs (the formula, a nacreous hour facet, the brief's worn-path ending), plus definition, quality, scope and constraint.
- A widening round ran: equal-weight lenticular and noctilucent sightings, options for hour, sound and kigo, and the nacreous facet rewritten as one sighting among several.
- **Round-2 verify still found `directive` narrowings** (the formula, the brief, the rarity facet funneling to the lens image). The agent says some nacreous emphasis remains in the brief. Lite has no second round, so it stays. The dump was used as built.
- Final check: 0 errors; candidate_pool_thin 1, oversized_entry 2.
- 21 agents.
- Main loop: 213,673 tokens, 1586 s (26.4 min).

## t1-button: dreamlike-button.metadump.json
- 94 entries, ~30.7K tokens (123 KB). Grounding 26/94 collected (28%), 12 hosts.
- Thesis: "What makes a hovered button read as dreamlike is that its light and its motion arrive at different moments, so the surface seems to still be waking up after the pointer has moved on; drift, bloom, float and shimmer are four ways of staging that delay."
- Angles: lingering settle, lit from within, quiet until touched, one light pass. Quality facets "dreamlike", "ethereal" and "practical" carry four readings each, no default.
- Discovery: 3 pages (web.dev animation performance, a glowing-button tutorial, a gist of named easings); no images, so no moodboard.
- Exports: `css-implementation` and `design-review`, no llm_brief. **Verify flagged `css-implementation` as close to a finished spec** (a copy risk under ADR 0010), and it was still there after the widening round.
- Verify, both rounds: contradictions against the researched hover band (a 500 ms glow reveal, an enter dial), and an alpha floor against "practical". Narrowings included `directive` in both rounds. A widening round ran (press and focus dials, values moved into the band, a scoped `not_wanted` for a background-position sweep). Round-2 findings remain at lite's cap.
- Final check: 0 errors, 0 warnings.
- 19 agents. Main loop: 200,822 tokens, 1612 s (26.9 min).
