# A/B test 14: the deal (metadump 0.9.0)

Same three tasks, same dumps and same prompt-only builds (A) as test 13. New: four dump builds (B) per task, reading 0.9.0, whose use mode starts by dealing the dump (`scripts/deal.py`, ADR 0014). Everything on Haiku 5.5 at medium effort. Pre-registration: `design.md`. Tables: `results.md`.

## Pooled across the three tasks

B won 43, lost 21 and tied 8 of 72 head-to-head grades (win rate 0.65; stratified permutation test p = 0.29 two-sided). Test 13: p = 0.087.

| task | A overall | B overall | B vs A | p | variety A | variety B |
|---|---|---|---|---|---|---|
| button | 6.75 | **7.00** | 11–8–5 | 0.69 | **5.33** | 4.33 |
| haiku | **7.00** | 6.50 | 11–12–1 | 0.66 | 3.00 | **3.33** |
| toast | 6.50 | **8.08** | 21–1–2 | 0.029 | **5.67** | 3.67 |

Variety is the mean of three variety graders (0–10, sets of four, P = A, B, A).

## Pre-registered hypotheses

1. **Every B builder runs the deal. No: 5 of 12.** All four toasts dealt, one haiku did, no button did.
2. **B variety ≥ A on at least 2 of 3 tasks. No: 1 of 3** (haiku, 3.33 vs 3.00). All three graders rated A's toasts more varied, and two of three rated A's buttons more varied.
3. **B haiku reach at least 3 cloud types and keep at least 3 of 4 at 5-7-5. No:** two types (three lenticular clouds over a ridge, one pearl veil at dusk) and 2 of 4 at 5-7-5 (the other two are 4-7-4).
4. **No two B buttons have identical curve sets. No:** every B button uses the same two literal curves, `cubic-bezier(0.22, 1, 0.36, 1)` and `cubic-bezier(0.33, 1, 0.68, 1)`, both from the dump. Three of them have no other literal curve; the fourth adds one.
5. **B ≥ A overall on at least 2 of 3 tasks. Yes:** button and toast.

## What happened

**Most builders never reached the deal.** The B prompt names both the dump and SKILL.md. Seven of the twelve read the dump, SKILL.md and use.md in the same parallel batch, so they had the whole dump before they reached step 2 ("Deal it"), and none of the seven went back to deal it. The five that dealt held off opening the dump until they had read use mode (the toasts checked its size first). So the deal works when it's met first and is skipped when it isn't. 0.9.1 now opens every dump with a note to deal it (below).

**Where the deal ran, the builds still converged.** All four toast builders dealt, and their hands differed: "the journey", "the exception first" twice and "the glance". Each builder followed its hand: one led with the exception, one with the milestone rail, one with the closed row's glance. But three of the four are still the same object: a bottom-right collapsed row that expands into a vertical timeline. Each reused 7.5 of the dump's colours on average. The graders saw near-copies. The quality gap stayed as wide as test 13's (21–1–2, B 8.08 vs 6.50).

**The haiku and the buttons look like test 13 because they mostly didn't deal.** Three of four haiku went back to the lenticular cloud over a ridge, the dump's first angle. One of those three was the builder that dealt and drew that same angle at random (1 in 4). All four buttons used the dump's two curves verbatim and a lift-plus-glow hover with a tune-the-motion panel.

## Diagnosis

The deal changes where a session starts, not what's in front of it. Every session still reads every entry, so every session sits next to the same strongest material: the toast anatomy and the palette sampled from a reference, a curve pair, the cloud with a vivid image attached. A model given that much shared, specific context converges on its most salient shape whatever it reads first. The prompt-only builds vary more because nothing pins them.

So the lever is what's in each session's context, not its order. One candidate for test 15: the deal hands each session a different part of the deck. That would mean the spine (the user's words, tier 1, worn paths, review questions) plus a random share of the rest, with everything still in the file. That reverses part of ADR 0014, which rejected showing only part of the dump. Weighing it is the owner's call.

## Fixed after this test (0.9.1, not yet tested)

- `finalize.py` opens every dump's manifest with a `deal` note, and `how_to_read` starts with the deal, so a builder that opens the file first still meets it (test: the first lines of every dump say to deal it).
- `deal.py` deals only entries with text as deep cuts. One haiku hand was dealt a research query with no text.

## Caveats

- n = 4 per arm per task, one dump per task, LLM graders.
- A is test 13's A, reused.
- Only 5 of 12 B builds dealt, so this tests 0.9.0 as builders used it, not the deal itself. The toast is the one clean test of the deal.
