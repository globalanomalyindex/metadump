# A/B test 15: a hand, not the deck (metadump 0.10.0), Sonnet 5.5 at medium

Same three tasks as tests 12 to 14. New:
- **Model:** builders and graders on Sonnet 5.5 at medium effort, both arms built fresh (the owner asked for Sonnet).
- **The deal:** each session now gets a hand (ADR 0015): the user's words, tier 1, worn paths and review questions, plus a random half of everything else.

The dumps are test 13's (Haiku-built), re-finished so every dump opens with the deal. Pre-registration: `design.md`. Tables: `results.md`.

## Results

| task | A overall | B overall | B vs A (won–lost–tied) | p | variety A | variety B |
|---|---|---|---|---|---|---|
| button | **7.83** | 6.42 | 1–21–2 | 0.057 | 3.00 | **4.00** |
| haiku | 5.42 | **7.75** | 21–1–2 | 0.057 | 1.33 | **5.33** |
| toast | 7.33 | 7.33 | 8–10–6 | 1.0 | **4.33** | 3.33 |

Pooled: 30 wins, 32 losses, 10 ties (p = 0.55). Variety is the mean of three variety graders (0–10).

## Pre-registered hypotheses

1. **At least 10 of 12 B builders deal. Yes: 12 of 12** (test 14: 5 of 12). The note at the top of every dump reached the builders that open the file first.
2. **B variety ≥ A on at least 2 of 3 tasks. Yes: button and haiku**, the first time since test 12. All three graders rated B's haiku more varied, two of three B's buttons. Two of three rated A's toasts more varied.
3. **B ≥ A overall on at least 2 of 3 tasks. Only by a tie:** haiku B, toast level at 7.33 each, button A by 1.4 points.
4. **No two B buttons share a curve set, and the B haiku reach 3 cloud types. Half:** all four button curve sets differ, but the haiku reach two clouds (nacreous twice, lenticular twice).
5. **On the toast, B ≥ A. Only by a tie** (7.33 each, 8–10–6 head to head).

## What happened

**The haiku is the clearest win the dump has had on this task.**
- All four prompt-only haiku are the same poem: nacreous, mother-of-pearl, dusk or dawn, and two of them have "the sky holds". Variety 1.33.
- The dump haiku came from two hands: "twilight colour" (a pearl veil after sunset) and "the watcher's first sky" (a lens cloud over a ridge, a cold cup on the sill, the smell of snow).
- All four dump haiku are 5-7-5, and they won form 9.08 vs 6.67 and freshness 7.42 vs 4.58.

**The button lost, and the cause is in the dump, not the deal.**
- The prompt-only buttons went big: a "blooming blurred halo", an "iridescent pill", a "drifting light blob". Graders rated them dreamlike 8.25.
- The dump buttons were careful and quiet. Graders called them "a modest blue smudge" and "fairly subtle"; dreamlike 6.17. They won practical (7.83 vs 7.08) and lost everything else.
- The dump's worn paths list nearly every classic dreamlike move as not wanted (glow, glass, bounce, fade, idle drift), and each comes with a tamer replacement: "a faint blurred halo", "a soft tinted glow only on hover, at low opacity". So the dump narrows "dreamlike" toward restraint, the kind of narrowing of the user's own word that ADR 0013 rules out. The Haiku-built dump got past verify with it.
- The hand made it worse. Every hand keeps the worn paths whole and halves the material to play with, so a hand is roughly twice as much "avoid this" as the full dump.
- Two of the four hands also started from "keyboard parity", an angle about focus states rather than a way into a dreamlike button.

**The toast lead is gone, because Sonnet's prompt-only toasts are good.**
- Sonnet's prompt-only toasts scored 7.33, against 6.08 and 6.50 for Haiku's in tests 13 and 14. The dump toasts scored 7.33 too, against 8.08 for Haiku's (different graders, so only a rough guide).
- The dump toasts led on compact, usability and collapsible. The A toasts led on tracking: the dump's very compact closed rows left out the ETA.
- Three of four dump toasts started from "the glance", and they converge again: a bottom-right card with a vertical timeline.

**Copying went down.** No B button reuses a whole curve set. Three reuse one to three of the dump's curves verbatim, and one reuses none. Each B toast reuses 3.5 dump colours on average, down from 7.5 in test 14.

## Diagnosis

- **The hand works as a mechanism:** every builder dealt, and variety rose on two of three tasks.
- **What's left is the dump's voice.**
  - Worn paths that hand over tamer replacements narrow the user's quality words, and a hand keeps all of them while it halves everything else.
  - Angles that are sub-concerns (keyboard parity) waste a hand's starting point.
- **Candidates for the next round:**
  - deal the worn paths like everything else, so a hand's ratio of avoid to explore stays the dump's;
  - write a worn path's "instead" as a spread in both directions, bolder as well as quieter, never a single tamer substitute;
  - have verify check that every angle is a way into the whole request.

## Caveats

- n = 4 per arm per task, one dump per task (Haiku-built, while the builders are Sonnet), LLM graders.
- Two p values are 0.057, the second-smallest possible at n = 4 with ties; neither is below 0.05.
- With Sonnet on both arms, test 15 can't be compared number for number with tests 13 and 14.
- Hands repeat by chance: each dump has four or five angles, so with four builders two often start from the same one (it happened on every task).
- An installed design hook (impeccable) commented on HTML files inside builder sessions. It fires on any HTML write, so it applied to both arms; two B builders reported keeping a glow it flagged.
