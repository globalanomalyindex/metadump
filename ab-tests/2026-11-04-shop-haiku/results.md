# A/B test 3 results: compact shopping component, Haiku everything

Arms: **A** = task only; **B** = task + metadump 0.3.0 (lite, with discovery)

## Blind grader scores (0-10; 4 runs per arm x 3 graders = 12 scores per arm)

| arm | overall | compact | minimal | modern | usability | craft | mean rank (1-4) | overall per run |
|---|---|---|---|---|---|---|---|---|
| A | **7.04** | 7.33 | 6.17 | 6.58 | 8.58 | 6.92 | 2 | 6.5, 7.33, 7.67, 6.67 |
| B | **6.33** | 5.67 | 8.42 | 6.42 | 6.75 | 7.25 | 3 | 6.83, 6.17, 6.33, 6.0 |

## Head to head (same grader, same block, overall)

- **B vs A**: 6 wins, 16 losses, 2 ties (win rate 0.29)

Grader agreement: mean pairwise Pearson r = -0.09.

## Does it work? (headless Chrome: click the main shopping action, click +, check 390 px)

| arm | works | action found | action changes page | qty control | qty changes | no overflow at 390 px | JS errors | unnamed buttons |
|---|---|---|---|---|---|---|---|---|
| A | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 0 | 2 |
| B | **4/4** | 4/4 | 4/4 | 0/4 | 0/4 | 4/4 | 0 | 0 |

## Cost per build run (Haiku)

| arm | runs | mean tokens | mean seconds | mean tool calls |
|---|---|---|---|---|
| A | 4 | 85153 | 50.8 | 3.2 |
| B | 4 | 123018 | 169.7 | 13.8 |

Dump build (one-off, Haiku main loop and workers): 144911 tokens reported for the main loop, 556 s.

## Grading rounds

**v2 (above) is the primary result.** Round v1 used mobile screenshots taken with `--window-size=390,844`. Headless Chrome won't make a window narrower than about 500 px, so those pages were laid out at about 500 px and cropped to 390. Every run looked clipped on the right, and nearly every v1 note penalized that. The click test, which emulates a real 390 px phone, found no overflow on any run. `mobile.mjs` re-shot the phones with true device emulation. The same six grader prompts and label orders then re-graded blind. v1 is kept in `v1/`.

| round | A overall | B overall | B vs A win rate | run-mean diff, exact permutation p (two-sided, 4 v 4) |
|---|---|---|---|---|
| v1 (cropped phone shots) | 7.17 | 5.58 | 0.12 | 1.58, p = 0.057 |
| v2 (true 390 px) | **7.04** | **6.33** | **0.29** | 0.71, p = 0.086 |

With 4 runs per arm, the smallest possible p is 0.029. This test can show a direction, not settle it. Both rounds point the same way.

## What happened

- **Hypothesis rejected.** B ≥ A overall did not hold. B won only on **minimal** (8.42 vs 6.17) and slightly on **craft** (7.25 vs 6.92). It tied on **modern** (6.42 vs 6.58) and lost on **usability** (6.75 vs 8.58) and **compact** (5.67 vs 7.33).
- **The dump narrowed the task.** Two tier-1 entries that the build *inferred* turned "compact" into "one product, four parts, a single add-to-cart":
  - "minimal part set": image, name, price, one add-to-cart, "nothing else is needed to shop".
  - "compact footprint": "one product ... in a single column".

  All four B builders followed them. They built sparse, near-identical card rows with no cart review, no quantity control and no checkout, and their tall cards left dead space. Graders read that as less compact and less usable. A's builders, unguided, built dense small storefronts with search, filters, steppers and a cart, and graders rewarded the complete shopping job.
- **The dump was mostly opinion, not collected facts.** Of 99 entries, 53 were inferred, 12 proposed, 18 unknown, 12 researched and 4 user_stated. All 15 anti-keywords were inferred. Discovery (lite: at most 1 video, 1 page, 6 images) found one usable page, a platform-specific product card spec. It found no readable video and no freely licensed images. So the dump carried little of the objective information the skill exists to collect.
- **Same lesson as test 2, from a different angle.** In test 2 a wrong concrete value overrode the user's words. Here an inferred *interpretation*, placed at tier 1, narrowed the user's words. The smaller model follows tier 1 closely either way.
- **What it did well.** B was consistently restrained and accessible: 0 unnamed buttons (A had 2), labeled variant radios, sold-out reasons, and loading, added and error states. It also respected its anti-keywords: no gradients, no emoji, no glass.
- **Cost.** B builders used 1.4x the tokens and 3.3x the time of A (they read the dump: about 14 tool calls vs 3). The dump build cost one Haiku main loop (145K tokens, 9 min) plus 8 Haiku workers.

## Skill changes this suggests

1. An *inferred* entry that narrows or redefines the task's scope ("compact means one product") shouldn't sit at tier 1. Where the prompt's noun has several readings ("shopping component": a product card, a cart, a product list, a checkout), the dump should keep them as `senses` and an open question with a default, not collapse to one.
2. Report the grounding mix at build time, and say so plainly when collected entries (researched, observed, measured) are a small share.
3. Bug found during the build: `finalize.py merge` crashes on an options group carrying an `_about` note. That's the pattern the briefs recommend. Reproduced on the repo copy; not fixed yet.

Contact sheet: `shots/shop-contact-sheet.png`. Dump: `metadumps/shop-component.metadump.json`.
