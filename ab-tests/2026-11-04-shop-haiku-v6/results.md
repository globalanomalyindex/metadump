# A/B test 6 results: the shopping test from scratch on metadump 0.5.1, Haiku everything

Arms: **A** = task only; **B** = task + metadump 0.5.1 (lite)

## Blind grader scores (0-10; 4 runs per arm x 3 graders = 12 scores per arm)

| arm | overall | compact | minimal | modern | usability | craft | mean rank (1-4) | overall per run |
|---|---|---|---|---|---|---|---|---|
| A | **6.42** | 5.75 | 6.5 | 6.5 | 7.0 | 6.83 | 3 | 5.67, 6.33, 6.0, 7.67 |
| B | **7.5** | 7.42 | 8.08 | 7.0 | 8.25 | 7.25 | 2 | 7.67, 8.0, 7.67, 6.67 |

## Head to head (same grader, same block, overall)

- **B vs A**: 17 wins, 5 losses, 2 ties (win rate 0.75)

Grader agreement: mean pairwise Pearson r = 0.6.

## Does it work? (headless Chrome: click the main shopping action, click +, check 390 px)

| arm | works | action found | action changes page | qty control | qty changes | no overflow at 390 px | JS errors | unnamed buttons |
|---|---|---|---|---|---|---|---|---|
| A | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 0 | 4 |
| B | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 0 | 7 |

## Cost per build run (Haiku)

| arm | runs | mean tokens | mean seconds | mean tool calls |
|---|---|---|---|---|
| A | 4 | 88504 | 68.5 | 3.8 |
| B | 4 | 160458 | 238.2 | 15.8 |

Dump build (one-off, Haiku main loop and workers): 183874 tokens reported for the main loop, 1934 s.

Exact two-sided permutation test on run means: B − A = +1.08, p = 0.114 (8 of 70). With 4 runs per arm the smallest possible p is 0.029, so this shows a direction, not a settled result.

## What happened

- **Both pre-registered targets were met.** B ≥ A overall (7.50 vs 6.42; B won 17 of 24 head-to-head pairs, lost 5, tied 2). B's usability rose to 8.25, above A's 7.0. In test 5, B's usability trailed A's (6.75 vs 7.58). Graders agreed (r = 0.60).
- **B led on every criterion:** compact 7.42 vs 5.75, minimal 8.08 vs 6.5, modern 7.0 vs 6.5, usability 8.25 vs 7.0, craft 7.25 vs 6.83.
- **The whole job is covered now.** Every B build has size or variant choice, a quantity stepper, add to bag with pending, added and error states, sold-out handling (often with "Notify me"), and a bag drawer for review that reaches checkout. The drawer traps focus and becomes a bottom sheet on phones. Graders called these "the strongest shopping logic" and "a real component". The dump's default reading ("a product card whose one add control feeds a mini bag that reaches checkout") and its seven-step `essence.task.job` show up directly in the builds.
- **A this time** is ordinary storefronts with no bug like test 5's A-r2. Graders' complaints: initials or gradient placeholder tiles, no variant or quantity on the card, catalogue pages rather than components, and a cart buried below the products on phones.
- **What B still gets wrong:**
  - On phones, several builds show one card per screen, which wastes the footprint.
  - On desktop, 3 or 4 cards leave the canvas mostly empty.
  - Add buttons sit at different heights across cards.
  - B has 7 buttons without an accessible name (A: 4), mostly icon-only steppers and swatches. That's the opposite of test 5, where B had 0.
- **The dump** (`metadumps/shopping-component.metadump.json`):
  - **Size and grounding:** 195 entries, 26% collected, sources from 8 hosts.
  - **Task ladder and job:** recorded; the job runs pick → see price and variant → choose options and quantity → add → see the bag → review it → check out.
  - **Readings:** 5, with a default that covers the whole job.
  - **Widening and re-verify:** one widening round ran, then verify re-ran on the rebuilt dump (as 0.5.1 intends). Two tier-2 contradictions went to open questions.
  - **Discovery:** 3 pages (2 screenshotted); no readable video or free images; Baymard thumbnails were robots-disallowed.
  - **Moodboard:** kept 2 real screenshots and no logos or blanks, so the noise filter worked.
- **Cost:** B builders used 1.8× the tokens and 3.5× the time of A (16 tool calls vs 4). The dump build was one Haiku main loop (184K tokens reported, 32 min) plus 20 Haiku workers.
- **Harness note:** the click test first reported 3 B runs as broken. It read the add button's label after clicking it, and these buttons turn into spinners. With the label read before the click, all 8 work. That bug didn't change tests 3 or 5, whose buttons kept their text.

## Across the three shopping tests

| | test 3 (0.3.0) | test 5 (0.5.0) | test 6 (0.5.1) |
|---|---|---|---|
| A overall / B overall | 7.04 / 6.33 | 5.58 / 7.17 | 6.42 / **7.50** |
| B vs A win rate | 0.29 | 0.83 | 0.75 |
| B usability vs A usability | 6.75 vs 8.58 | 6.75 vs 7.58 | **8.25 vs 7.0** |
| B builds with a bag review and checkout | 0 / 4 | few | **4 / 4** |
| dump: entries, collected, hosts | 99, 16%, 1 | 189, 31%, 13 | 195, 26%, 8 |

Different graders and fresh A arms each time, so compare directions, not decimals.

Contact sheet: `shots/shop-v6-contact-sheet.png`.
