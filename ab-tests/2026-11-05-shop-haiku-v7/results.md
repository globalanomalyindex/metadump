# A/B test 7 results: the shopping test from scratch on a one-agent build (an unshipped draft, scrapped), Haiku everything

Arms: **A** = task only; **B** = task + the one-agent draft

## Blind grader scores (0-10; 4 runs per arm x 3 graders = 12 scores per arm)

| arm | overall | compact | minimal | modern | usability | craft | mean rank (1-4) | overall per run |
|---|---|---|---|---|---|---|---|---|
| A | **6.17** | 6.33 | 6.0 | 5.5 | 8.33 | 6.25 | 3 | 7.0, 6.33, 5.0, 6.33 |
| B | **6.92** | 7.08 | 8.58 | 7.42 | 7.08 | 6.75 | 2 | 6.33, 8.0, 5.33, 8.0 |

## Head to head (same grader, same block, overall)

- **B vs A**: 15 wins, 6 losses, 3 ties (win rate 0.69)

Grader agreement: mean pairwise Pearson r = 0.6.

## Does it work? (headless Chrome: click the main shopping action, click +, check 390 px)

| arm | works | action found | action changes page | qty control | qty changes | no overflow at 390 px | JS errors | unnamed buttons |
|---|---|---|---|---|---|---|---|---|
| A | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 0 | 5 |
| B | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 0 | 0 |

## Cost per build run (Haiku)

| arm | runs | mean tokens | mean seconds | mean tool calls |
|---|---|---|---|---|
| A | 4 | 90314 | 65.3 | 3.5 |
| B | 4 | 120293 | 154.1 | 10.8 |

Dump build (one-off, one Haiku agent plus any helpers it sent): 150177 tokens reported for the agent, 162 s.

Exact two-sided permutation test on run means: B − A = +0.75, p = 0.486 (34 of 70). With 4 runs per arm the smallest possible p is 0.029, so this shows a direction, not a settled result.

## What happened

- **The build got much faster.** One Haiku agent built the dump in 2.7 minutes (162 s, 150K tokens, 26 tool calls, no helpers). In test 6, a Haiku main loop and 20 Haiku workers took 32 minutes. B's builders also got cheaper (120K tokens and 154 s per build, against 160K and 238 s in test 6), because the dump is smaller.
- **B still beat A, by less.**
  - Overall: B 6.92 vs A 6.17; B won 15 of 24 head-to-head pairs, lost 6 and tied 3 (win rate 0.69). Graders agreed (r = 0.60).
  - B led on compact (7.08 vs 6.33), minimal (8.58 vs 6.0), modern (7.42 vs 5.5) and craft (6.75 vs 6.25).
  - The run means overlap a lot (p = 0.49), so this result is weaker than test 6's.
- **Usability fell behind again: B 7.08 vs A 8.33.** It's the same pattern as test 5, which 0.5.1 had fixed. Only B-r4 (8.0) has a sticky bag bar with checkout always reachable.
  - B-r2 (8.0 overall) has an inline bag and subtotal but no checkout action.
  - B-r1 (6.33) hides its checkout inside a collapsed bag bar.
  - B-r3 (5.33) hides checkout behind a bag toggle and clips its "Add to bag" label on desktop.

  All four A builds are full storefronts with a cart drawer and checkout.
- **The cause is in the dump.**
  - Its own `essence.task.job` ends with "review the bag or check out", but the default reading ("one product card with quick add and a compact confirmation") stops at the confirmation.
  - The cart open question defaults to "a compact bag count and a line for the item only".
  - Create mode's self-check ("does the default reading cover the user's whole job?") didn't catch this, and no verify pass exists any more to catch it. Test 3 showed the same narrowing failure.
- **The dump is thinner than test 6's:**
  - 58 entries (create.md asks for 60 to 150), 21% collected, sources from 4 hosts (test 6: 195 entries, 26%, 8 hosts);
  - 6 searches, 7 pages read as text;
  - no screenshots, images or moodboard, though the task is visual and create.md asks for exemplar pages and images;
  - no exemplars section and only 3 associations.

  Its quotes came from WebFetch's summaries and weren't checked against the pages.
- **What B got right:** every B build has 0 unnamed buttons (A: 5), with labeled steppers, live feedback and sold-out or low-stock states. Graders praised the restrained line art and single accent, against A's emoji or initials tiles.
- **All 8 builds work** in the click test, with no JS errors and no overflow at 390 px.

## Hypothesis check

- Dump built in 15 minutes or less: **met** (2.7 minutes).
- B ≥ A overall: **met** (6.92 vs 6.17), with the margin shrinking from test 6, as expected.
- Not pre-registered as a target, but worth noting: B's usability dropped below A's, because the one-agent dump narrowed the default reading.

## Across the four shopping tests

| | test 3 (0.3.0) | test 5 (0.5.0) | test 6 (0.5.1) | test 7 (one-agent draft) |
|---|---|---|---|---|
| dump build | swarm | swarm | swarm, 32 min | **one agent, 2.7 min** |
| A overall / B overall | 7.04 / 6.33 | 5.58 / 7.17 | 6.42 / **7.50** | 6.17 / **6.92** |
| B vs A win rate | 0.29 | 0.83 | 0.75 | 0.69 |
| B usability vs A usability | 6.75 vs 8.58 | 6.75 vs 7.58 | **8.25 vs 7.0** | 7.08 vs 8.33 |
| B builds with a reachable checkout | 0 / 4 | few | **4 / 4** | 1 / 4 always visible, 3 / 4 at all |
| dump: entries, collected, hosts | 99, 16%, 1 | 189, 31%, 13 | 195, 26%, 8 | 58, 21%, 4 |

Different graders and fresh A arms each time, so compare directions, not decimals.

Contact sheet: `shots/shop-v7-contact-sheet.png`.
