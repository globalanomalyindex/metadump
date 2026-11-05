# A/B test 8 results: three "sticky and punchy" bezier curves as loops, metadump 0.7.0 (facets), Haiku everything

Arms: **A** = task only; **B** = task + metadump 0.7.0 (facets, lite)

## Blind grader scores (0-10; 4 runs per arm x 3 graders = 12 scores per arm)

| arm | overall | sticky | punchy | distinct | presentation | craft | mean rank (1-4) | overall per run |
|---|---|---|---|---|---|---|---|---|
| A | **4.83** | 4.75 | 5.0 | 6.67 | 3.58 | 4.42 | 2.58 | 5.67, 7.33, 1.0, 5.33 |
| B | **6.17** | 4.83 | 5.42 | 3.83 | 8.17 | 7.25 | 2.42 | 6.0, 6.0, 7.0, 5.67 |

## Head to head (same grader, same block, overall)

- **B vs A**: 13 wins, 9 losses, 2 ties (win rate 0.58)

Grader agreement: mean pairwise Pearson r = 0.68.

## Does it work? (headless Chrome: window.CURVES valid, loops animate, animations use the declared curves, 390 px)

| arm | works | CURVES valid | animating | uses declared curves | no overflow at 390 px | JS errors |
|---|---|---|---|---|---|---|
| A | **3/4** | 4/4 | 3/4 | 3/4 | 4/4 | 1 |
| B | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 | 0 |

## Cost per build run (Haiku)

| arm | runs | mean tokens | mean seconds | mean tool calls |
|---|---|---|---|---|
| A | 4 | 80914 | 37.3 | 3 |
| B | 4 | 128273 | 99.0 | 10.2 |

Dump build (one-off, Haiku main loop plus Haiku workers): 184371 tokens reported for the main loop, 1825 s.

Exact two-sided permutation test on run means: B − A = +1.34, p = 0.457 (32 of 70). With 4 runs per arm the smallest possible p is 0.029, so this shows a direction, not a settled result.

## What happened

- **B "won" mostly because one A build was broken.**
  - A-r3 throws a ReferenceError at load (`blurbs` read before its `const`), so its page is blank, and every grader gave it 1/10.
  - Without it, A's three working builds average 6.11, against B's 6.17. On the curves themselves, the arms are tied.
- **Where B won: presentation (8.17 vs 3.58) and craft (7.25 vs 4.42).** Every B build has:
  - a graph per curve, with a live marker;
  - measured readouts (overshoot, rest-by), copyable values and per-card play or pause;
  - a working reduced-motion path.

  The A builds show small loops with little or no explanation, and two have no reduced-motion handling at all.
- **Where B lost: distinct (3.83 vs 6.67).**
  - All four B builds use nearly the same three curves: the dump's proposed "default set" (`[0.2, 1.2, 0.2, 1]`, `[0.15, 1, 0.2, 1.04]`, `[0.18, 0.98, 0.3, 1]`). B-r3 swapped one for another option from the dump.
  - All are fast ease-outs with 0–5% overshoot lasting 250–350 ms, so graders called them "near-identical".
  - The A builds spread across a slow-start "grip" S-curve, a 5–10% overshoot and an anticipation wind-up.
- **Sticky and punchy came out tied** (sticky 4.83 vs 4.75, punchy 5.42 vs 5.0). The dump didn't make the curves feel more sticky or punchy.
- **Why the curves collapsed:** the dump decided what the words mean and then optimized for its own definition.
  - It defined sticky as "within 1 percent of rest by about 0.65 of the run, a held rest" and punchy as "90 percent of the distance by x ≈ 0.27, a 2 to 5 percent overshoot". Both were inferred at tier 2; no source defines them.
  - It also said sticky "never implies slow or long crawl", which ruled out the slow-start grip reading behind A's best curves.
  - The verify and widening rounds then tuned the proposed curves against that self-made band, which tightened the definition instead of widening it.
  - The readings kept scope options (three curves as loops, one hero curve, a curve family, a picker), but not the different meanings of "sticky". Every B builder copied the one concrete set it was given. Test 2 failed the same way: the smaller model follows concrete numbers.
- **The facet shape held up.**
  - 53 of the 96 entries are facets with properties, behaviors and principles.
  - The dump opens with a thesis ("punchy is the start and sticky is the stop"), a summary, a formula with roles, and tensions.
  - Only one `wordy_entry` warning fired, against 79 in the 0.6.0 shopping dump.
- **The size didn't hold up.**
  - 96 entries and about 52.8K tokens, against a lite target of 8–15K.
  - 25K of that is the search index: indexing every facet phrase, word by word, doubled it.
  - The body is about 22K, and the `curves` section alone is 8K.
- **Cost:**
  - dump build: 30 minutes, 19 Haiku agents (one widening round, verify re-run);
  - B builds: 128K tokens and 99 s each, against 81K and 37 s for A.

## Hypothesis check

- B ≥ A overall: **met on paper** (6.17 vs 4.83), but it's a tie once the broken A build is set aside.
- B's curves more distinct and more deliberately sticky and punchy: **not met.** They were less distinct (3.83 vs 6.67), and sticky and punchy were tied.
- Dump far smaller than 0.6.0 dumps: **not met** (52.8K tokens, with half of it index).

## What changed in 0.7.0 after this test (ADR 0010; not retested yet)

1. Keep the readings of each quality, not just of the scope. "Sticky" in motion can mean a slow start that grips, an early settle that holds, an overshoot that snaps back, or a magnetic pull. Put them side by side, as the shopping dumps did with scope.
2. Never propose one concrete default answer set for a creative task. Propose one option per reading, spread across them, so builders pick and mix instead of copying.
3. Verify should report a definition the build made up and then optimized against, as a narrowing.
4. Facet phrases (properties, descriptors, signals) are no longer indexed; grep finds them. On this dump that alone takes the file from 52.8K to 37.8K tokens.
5. Also: a facet over ~300 tokens warns (16 here), a section left with only notes is dropped (3 here), and `open_questions` defaults may settle a parameter but never the deliverable or a reading.
