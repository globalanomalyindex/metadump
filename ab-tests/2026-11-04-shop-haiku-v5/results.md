# A/B test 5 results: the shopping test from scratch on metadump 0.5.0, Haiku everything

Arms: **A** = task only; **B** = task + metadump 0.5.0 (lite)

## Blind grader scores (0-10; 4 runs per arm x 3 graders = 12 scores per arm)

| arm | overall | compact | minimal | modern | usability | craft | mean rank (1-4) | overall per run |
|---|---|---|---|---|---|---|---|---|
| A | **5.58** | 5.0 | 5.83 | 5.75 | 7.58 | 5.08 | 3.17 | 6.33, 3.67, 5.67, 6.67 |
| B | **7.17** | 8.25 | 8.25 | 6.67 | 6.75 | 6.5 | 1.83 | 7.0, 7.67, 6.33, 7.67 |

## Head to head (same grader, same block, overall)

- **B vs A**: 19 wins, 3 losses, 2 ties (win rate 0.83)

Grader agreement: mean pairwise Pearson r = 0.67.

## Does it work? (headless Chrome: click the main shopping action, click +, check 390 px)

| arm | works | action found | action changes page | qty control | qty changes | no overflow at 390 px | JS errors | unnamed buttons |
|---|---|---|---|---|---|---|---|---|
| A | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 0 | 5 |
| B | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 0 | 0 |

## Cost per build run (Haiku)

| arm | runs | mean tokens | mean seconds | mean tool calls |
|---|---|---|---|---|
| A | 4 | 86418 | 60.2 | 3.5 |
| B | 4 | 134338 | 121.0 | 14.2 |

Dump build (one-off, Haiku main loop and workers): 184955 tokens reported for the main loop, 1665 s.

Exact two-sided permutation test on run means: B − A = +1.58, p = 0.086 (6 of 70; with 4 runs per arm the smallest possible p is 0.029).

## What happened

- **Hypothesis held: B ≥ A overall.** B won 19 of 24 head-to-head pairs (3 losses, 2 ties). Graders agreed (r = 0.67, vs −0.09 in test 3). B led on compact (8.25 vs 5.0), minimal (8.25 vs 5.83), modern (6.67 vs 5.75) and craft (6.5 vs 5.08). **A still led on usability** (7.58 vs 6.75).
- **A was weaker than in test 3** (5.58 vs 7.04). A-r2 had a CSS bug: its tag pills inherited a 64 px swatch rule and covered the product art, and it scored 3.67. Without it, A is 6.22, still below B's 7.17, and every B run (6.33 to 7.67) scored at or above A's mean. A's other notes repeat across runs: emoji or initials as product art, tall cards, mobile headers flush to the edge.
- **The 0.5.0 dump stopped narrowing.** All four B runs kept the shopping flow: a dense four-across grid, add to bag turning into an inline stepper, a bag count, sold-out states with reasons, and live status text. The click test found a working quantity control in 4 of 4 B runs (test 3's B: 0 of 4). B had 0 unnamed buttons (A: 5).
- **Where B still loses: usability.** Graders flag "no cart review or checkout" on most B runs. The dump kept "mini cart with quantity" and "checkout summary" as readings, but the builders took the default (product card) and didn't combine readings. Desktop labels also wrapped ("Add to / bag", "2 in / bag"), and long names truncated.
- **The dump itself** (`metadumps/shop-component.metadump.json`):
  - **Size and grounding:** 189 entries, 31% collected (59), sources from 13 hosts.
  - **Task ladder:** UX design, UI design, interaction design, e-commerce, accessibility and front-end, down to values.
  - **Readings and routes:** 5 readings, an "explore options" route.
  - **Widening round:** one ran (verify found about 26 narrowings and 6 contradictions; all fixed), and the final build had 0 warnings. Caveat: verify was not re-run after the widening.
  - **Discovery:** 3 pages scraped and screenshotted; no readable video or free images, and several exemplar sites blocked fetching.
  - **Moodboard noise:** the moodboard also collected vendor logos and blank or all-white images from those pages.
- **Cost:** B builders used 1.6× the tokens and 2× the time of A (about 14 tool calls vs 3.5). The dump build: one Haiku main loop (185K tokens reported, 28 min) plus 16 Haiku workers.

## Compared with test 3 (0.3.0)

| | test 3 v2 (0.3.0) | test 5 (0.5.0) |
|---|---|---|
| A overall / B overall | 7.04 / 6.33 | 5.58 / **7.17** |
| B vs A win rate | 0.29 | **0.83** |
| B usability / compact | 6.75 / 5.67 | 6.75 / **8.25** |
| B runs with a quantity control | 0 / 4 | **4 / 4** |
| dump: entries, collected, hosts | 99, 16%, 1 | 189, 31%, 13 |

Different graders and a new A arm, so compare directions, not decimals.

## Next fixes this suggests

1. Moodboard noise: skip logos, tiny images and single-color images when collecting from pages.
2. Re-run verify after a widening round, so the repaired dump is checked too.
3. Usability: B builders took the default reading. Use mode could nudge "combine readings when the request allows it" more strongly, or the synthesis could make a richer default reading (a card with a mini cart).

Contact sheet: `shots/shop-v5-contact-sheet.png`.
