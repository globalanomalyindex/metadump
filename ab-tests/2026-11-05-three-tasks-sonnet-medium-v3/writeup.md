# A/B test 18: 0.11.0 plus the look (metadump 0.12.0), Sonnet 5.5 at medium

Use mode now ends with a look (ADR 0018): `look.py` renders the build headlessly, screenshots it at desktop and phone widths, hovers and opens it, and lists clipping, overlap, overflow and tiny targets for the builder to read before finishing. Everything else is test 16: the same 0.11.0 dumps (re-finished so their reading steps end with the look), the same prompt-only Sonnet builds, the same dump-arm prompt. Only the twelve dump builds and the graders are new. Pre-registration: `design.md`. Tables: `results.md`.

## Results

| task | A overall | B overall | B vs A (won–lost–tied) | p | variety A | variety B |
|---|---|---|---|---|---|---|
| button | 6.50 | **8.25** | 23–0–1 | 0.029 | 3.33 | **5.33** |
| haiku | 5.08 | **8.00** | 23–1–0 | 0.029 | 1.33 | **6.00** |
| toast | 6.83 | **7.50** | 11–7–6 | 0.51 | 3.00 | **6.33** |

Pooled: **57 wins, 8 losses, 7 ties** (win rate 0.84; stratified permutation test p = 0.0002). Grader agreement r = 0.90, 0.85, 0.79. All nine variety graders picked the dump side.

## Pre-registered hypotheses

1. **At least 9 of 12 B builders run the look. Yes: 8 of 8** that built something that renders (the four haiku builders had nothing to render). All 12 dealt. Every UI builder read at least one screenshot; five ran the look more than once and edited between looks.
2. **On the toast, B's craft ≥ 7.0 and the clipping complaints stop. Half:** craft 7.58 (test 16: 5.17). Two graders still named a "cut-off timeline" on B-r1 and B-r2. Those timelines are scrolling boxes (`overflow: auto`) whose last visible row straddles the edge, a case the look treated as deliberate scrolling. It reports it now (`cut-off`), added after these builds ran.
3. **B ≥ A overall on at least 2 of 3 tasks. Yes: 3 of 3.**
4. **B's variety ≥ A's on at least 2 of 3. Yes: 3 of 3** (test 16 too; test 17 was 1 of 3).
5. **Pooled, B wins more than it loses. Yes: 57–8–7** (test 16: 27–39–6).

## What happened

**The button flipped from 9–12–3 to 23–0–1 with the same dump.** The difference is what the builders did after the look. B-r2 ran the look five times, read six screenshots and edited twice between them. The graders' words moved from test 16's "modest", "quiet", "barely reads as ethereal" to "pointer-following bloom", "aurora halo blooms behind a white pill", "breathing glow layer". The best button of the eight (B-r3, 9.0 from all three graders) is "a slow lagging pointer-following light and rose-peach bloom, seven purposeful curves". Dreamlike: 8.42 vs 6.83.

**The toast went from 0–21–3 to 11–7–6.** Craft went from 5.17 to 7.58, the overlap and wrapped-row complaints are gone, and usability led 7.83 vs 6.58. Two complaints remain, both the scrolling-box case above. The dump toasts are also the most varied set on this task of any test (6.33): a top-centre pill, multi-parcel tabs, a segmented bar, an amber accent, a seven-step timeline.

**The haiku won again,** 23–1–0, with three cloud types (nacreous at dusk, a fallstreak hole with a plane's trail, noctilucent streaks) against the prompt-only side's one nacreous poem written four times. Form 9.08 vs 7.25, freshness 7.58 vs 4.50.

## A caveat on the absolute numbers

The prompt-only builds are the same files as in test 16, and their scores moved: button 7.50 to 6.50, toast 7.96 to 6.83, haiku 5.33 to 5.08. Graders score four builds in one block, so a build's number depends partly on its company; test 16's broken dump toasts made the same prompt-only toasts look better than they look next to working ones. The comparison that holds across tests is the head-to-head within a block, and that is what moved: 27–39–6 in test 16, 57–8–7 here, with the same A files.

## Across the Sonnet tests

| test | version | pooled (won–lost–tied) | p | more varied on |
|---|---|---|---|---|
| 15 | 0.10.0, a hand | 30–32–10 | 0.55 | 2 of 3 |
| 16 | 0.11.0, amplify, dumps rebuilt | 27–39–6 | 0.72 | 3 of 3 |
| 17 | 0.8.0 | 28–40–4 | 0.65 | 1 of 3 |
| 18 | 0.12.0, 0.11.0 plus the look | **57–8–7** | **0.0002** | 3 of 3 |

## Caveats

- n = 4 per arm per task, one dump per task (Haiku-built while the builders are Sonnet), LLM graders.
- A is reused from test 16; only B and the graders are new.
- The look is part of the dump arm's use mode and the prompt-only arm doesn't get one. A later test could give the prompt-only arm a look too, to separate the dump's contribution from the look's.
- The look's `cut-off` check was added after these builds ran, so these builds were made with a look that missed scrolling boxes.
- The impeccable design hook commented on HTML files inside builder sessions in both arms.
