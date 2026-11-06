# The four dumps (0.7.1 create mode, lite, Haiku 5.5 at low effort for the main loop and every worker)

Taken from each dump agent's report, plus `finalize.py check`. Main-loop usage only; worker usage is not in these numbers.

## t1-button: ethereal-button.metadump.json
- 73 entries, ~21.6K tokens (86,373 bytes). Grounding 21/73 collected (29%), 5 hosts.
- Discovery: 0 videos, 3 pages (all scraped), 0 images, so no moodboard.
- Verify: 0 contradictions. Narrowings by kind: write-button-css quality 4, job 1, constraint 3; check-output job 1, quality 1, constraint 4. Constraint findings no longer trigger a round (0.7.1).
- One widening round ran (job and quality narrowings). The gap shard added a placement facet and rewrote three facets as readings. It was rebuilt without re-normalize, re-synthesis or re-verify, so the placement facet is unrouted.
- Warnings at the final check: 9 (unrouted_section 1, undigested_source 1, oversized_entry 5, quality_one_reading 2). 0 errors. No finished deliverable in any entry.
- 16 agents. Main loop: 166,357 tokens, 625.8 s.

## t2-sandbox: physics-sandbox.metadump.json
- 60 entries, ~17.7K tokens (70,672 bytes). Grounding 18/60 collected (30%), 6 hosts.
- Discovery: 0 videos (one Drive link and one YouTube lesson rejected), 3 pages (Box2D mouse joint values, pymunk stack values, a Phaser index with no values), 0 images.
- Verify: 3 contradictions, between collected entries from the same scrape: a pinned held body versus integration, and release velocity versus pinning. 1 narrowing, of kind scope (a global anti-keyword `ak-no-reset` rules out the drag-only reading).
- **The widening round was not run.** Lite calls for one after a scope narrowing, but the main loop stopped before the gap planner. The narrowing and the contradictions are unresolved in the built dump. The dump was used as built.
- Final check: 0 errors, 0 warnings.
- 15 agents. Main loop: 170,227 tokens, 680.9 s.

## t3-poem: rare-clouds-poem.metadump.json
- 52 entries, ~16.8K tokens (67 KB). Grounding 15/52 collected (29%), 8 hosts.
- Discovery: not run (not a visual task, and no references were given).
- Verify: 0 contradictions. J2 found 2 narrowings (quality, plus a definition that pinned "short" to 2–4 stanzas). J3 found 5 (definition, two quality, two constraint). Copy pass clean.
- One widening round ran. It widened three quality facets to readings, researched 4 more formations (Kelvin-Helmholtz, mammatus, asperitas, fallstreak hole; lenticular and iridescent left unverified), and rewrote the synthesis, dropping the stanza-count pin. There was no second verify.
- Final check: 0 errors, 3 warnings (oversized_entry 2, wordy_entry 1). One leftover: an anti-keyword's `instead` still pins a stanza count. No finished poem in any entry or export; the verify sample poems stayed out of the dump.
- 15 agents.
- Main loop: 177,846 tokens, 723.7 s.

## t4-figma: figma-brand-loop-animation.metadump.json
- 51 entries, ~17.2K tokens. Grounding 10/51 collected (20%), 3 hosts. The final check has 1 warning: low_grounding.
- Discovery: 0 videos, 3 pages: Figma's 2024 brand-refresh blog, Figma Motion help, and a Rive blog post (thin). The W3C three-flash page was also fetched. The moodboard holds 14 page images (2 skipped), which are local only and not published.
- Build: 15 warnings (12 image_not_viewed) and 11 fixes, among them 5 brand-look entries demoted to inferred.
- No hex palette in the dump (`oq-brand-hex` is open: no fetched source gave hex values). No logo or asset copying in any entry.
- Verify: 0 contradictions. J2 found 1 quality narrowing ("motion never rests" ruled out continuous motion). J5 found 1 definition narrowing (the primitive-shapes check ruled out the hairline or soft-shadow reading).
- One widening round ran. The gap rewrote the motion facet and added a flat-solid reading. It could not edit the spine check, and there was no re-synthesis or re-verify, so the check still carries the single-definition wording.
- 15 agents. Main loop: 179,610 tokens, 790.0 s.

# Harness deviations (recorded as they happened)
- **Figma loop strips were blank in the first grading round.** `capture.mjs` loaded each frame sheet as one `data:` URL. Ten full-size frames went past Chrome's 2 MB URL limit, so 7 of 8 sheets rendered as blank white files. The button sheets (small crops) were fine. The six Figma graders saw no loop frames, and several said so. Fix: the sheet is written to a temp file and opened from there. The Figma task was recaptured, re-blinded with the same fixed label orders, and regraded by six fresh Haiku-low graders. The voided judgments are kept in `t4-figma/judgments-void/` and not counted.
- **Post-hoc loop measure.** The pre-registered seam metric (mean pixel difference between frames 5 s apart) only shows the timeline is periodic. It can't see a snap at the wrap, which two voided graders described. The recapture adds a dense frame-to-frame pass (about 80 quarter-scale frames over 5.5 s). It reports `max_jump_ratio`: the largest change per 100 ms over the median one, where high means a jump somewhere. It was added after the first capture, so it is a secondary, descriptive number.
