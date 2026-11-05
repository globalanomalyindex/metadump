# A/B test 2 results: mini music player, Haiku builders and graders

Arms: **A** = prompt only; **C** = hand-made metadata file; **B** = metadump + fixed skill

## Blind grader scores (0-10; 4 runs per arm x 3 graders = 12 scores per arm)

| arm | overall | fidelity | specificity | target fit | pitfalls avoided | mean rank (1-6) | overall per run |
|---|---|---|---|---|---|---|---|
| A | **6.42** | 7.42 | 6.67 | 6.42 | 6.08 | 2.67 | 6.0, 7.67, 7.0, 5.0 |
| C | **5.33** | 6.5 | 6.08 | 5.33 | 5.0 | 4 | 6.67, 4.33, 7.33, 3.0 |
| B | **5.58** | 6.58 | 6.0 | 6.0 | 5.5 | 3.83 | 4.67, 6.67, 5.67, 5.33 |

## Head to head (same grader, overall score)

- **B vs A**: 5 wins, 15 losses, 4 ties (win rate 0.29)
- **B vs C**: 13 wins, 11 losses, 0 ties (win rate 0.54)
- **C vs A**: 7 wins, 15 losses, 2 ties (win rate 0.33)

Grader agreement: mean pairwise Pearson r = 0.63.

## Does it actually work? (headless Chrome clicks play, waits, clicks next, pauses)

| arm | works | play found | advances while playing | next changes track | stops when paused | JS errors |
|---|---|---|---|---|---|---|
| A | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 | 0 |
| C | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 | 0 |
| B | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 | 0 |

## Cost per run (Haiku, medium effort)

| arm | runs | mean tokens | mean seconds | mean tool calls |
|---|---|---|---|---|
| A | 4 | 108363 | 143.6 | 4.8 |
| C | 4 | 113419 | 149.6 | 5 |
| B | 4 | 144520 | 181.9 | 12.5 |

## What it means

**Headline: on this task, with Haiku, the metadump arm lost.** Prompt-only scored 6.42, metadump 5.58, the hand-made file 5.33. B beat A in only 29% of head-to-heads and edged C (54%). Grader agreement was much better than test 1 (mean r = 0.63 across three graders vs 0.24 with two), so this result is more trustworthy than test 1's per-task numbers.

**Everything works.** All 12 players pass the click test (play, progress advances, next changes track, pause stops, zero JS errors). Differences are purely design.

**Why B lost (from every B note):** "the card reads as an opaque pale plate rather than translucent acrylic." The cause is in the dump, not the skill rules. Its landing-page section says in words that "color lives inside the material…tinted slab, not a colored or frosted fill" (tier 1), but its concrete parameters specify acrylic tint at 8–28% alpha over a #F6FAFF near-white page field, #EAF4FF text plates and navy ink. Following the numbers literally produces a pale plate. Haiku follows hex values and alphas over prose, and over the new "keep both poles / user_stated outranks proposed" rule. The dump was a lite build (no normalize, no audit, no gap round), so nothing caught the contradiction between its own tier-1 invariant and its tier-2 tokens.

**Other failures, all arms:** cards taller than the 800 px viewport (A-r4, B-r3, B-r4, C-r2, C-r4), blank prev/next icons (B-r1, C-r2).

**Cost:** B used 33% more tokens (145K vs 108K) and 12.5 tool calls vs 4.8. That's down from 21 in test 1 (lean-reading fix, though the model differs too).

## Fixes this points at

1. **Verify must test parameters against tier 1, not just look for guesses.** Add a contradiction pass: for each tier-1 entry, follow the routed parameters literally (render or sketch them) and check the result still satisfies it. Here it would have flagged that 8–28% alpha on near-white cannot read as "transparent blue acrylic".
2. **Concrete values beat prose, especially for smaller models.** Every tier-1 visual quality needs a parameter that produces it (e.g. a card tint alpha range that reads as colored acrylic), not only a sentence.
3. **Don't ship lite dumps for multi-consumer visual work without the audit.** Lite skipped normalize and audit to save cost; that is exactly where this contradiction would have been caught.
